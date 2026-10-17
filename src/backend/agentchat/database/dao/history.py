from datetime import datetime, timedelta, timezone
from typing import List

from sqlmodel import Session, delete, select, update

from agentchat.database.models.conversation import ConversationTable
from agentchat.database.models.history import HistoryTable
from agentchat.database.session import async_session_getter
from agentchat.utils.conversation_title import fallback_conversation_title


class HistoryDao:

    @classmethod
    async def create_history(cls, role: str, content: str, events: List[dict], conversation_id: str, token_usage: int = 0):
        """保存消息，首条用户消息同时设置短标题并标记异步生成机会。"""
        history = HistoryTable(
            content=content,
            role=role,
            events=events,
            conversation_id=conversation_id,
            token_usage=token_usage
        )
        async with async_session_getter() as session:
            # 先锁定会话行，再判断是否已有用户消息，避免同时发送时重复触发标题任务。
            activity = await session.exec(update(ConversationTable).where(
                ConversationTable.conversation_id == conversation_id).values(update_time=datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)))
            if not activity.rowcount:
                raise ValueError("会话不存在")
            # 保留微秒时间，确保同一秒内连续发送和回复的顺序稳定。
            history.create_time = datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)
            history.update_time = history.create_time
            first_user = False
            title = None
            if role == "user":
                previous = (await session.exec(select(HistoryTable.id).where(
                    HistoryTable.conversation_id == conversation_id, HistoryTable.role == "user").limit(1))).first()
                first_user = previous is None
                if first_user:
                    title = fallback_conversation_title(content)
                    await session.exec(update(ConversationTable).where(
                        ConversationTable.conversation_id == conversation_id).values(name=title))
            session.add(history)
            await session.commit()
            await session.refresh(history)
            return {
                "history_id": history.id,
                "first_user": first_user,
                "title": title,
            }

    @classmethod
    async def select_history_from_time(cls, conversation_id: str, k: int) -> List[HistoryTable]:
        """Select recent k history records for a conversation"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.conversation_id == conversation_id
            ).order_by(HistoryTable.create_time.desc())
            result = await session.exec(statement)
            messages = result.all()

            # 每次最多取当前会话的k条历史记录
            if len(messages) > k:
                messages = messages[:k]
            # 保持消息的时间顺序（从旧到新）
            messages.reverse()

            return messages

    @classmethod
    async def get_conversation_history(cls, conversation_id: str):
        """Get all history records for a conversation ordered by time"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.conversation_id == conversation_id
            ).order_by(
                HistoryTable.create_time
            )
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def delete_history_by_conversation_id(cls, conversation_id: str):
        """Delete all history records for a conversation"""
        async with async_session_getter() as session:
            statement = delete(HistoryTable).where(HistoryTable.conversation_id == conversation_id)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def get_short_term_messages(cls, conversation_id, summary_last_time):
        """Get short term history messages"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.conversation_id == conversation_id,
                HistoryTable.create_time > summary_last_time
            ).order_by(
                HistoryTable.create_time
            )

            result = await session.exec(statement)
            return result.all()
