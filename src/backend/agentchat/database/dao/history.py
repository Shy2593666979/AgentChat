from typing import List

from agentchat.database.models.history import HistoryTable
from sqlmodel import Session, select, delete
from agentchat.database.session import async_session_getter

class HistoryDao:

    @classmethod
    async def create_history(cls, role: str, content: str, events: List[dict], dialog_id: str, token_usage: int = 0):
        """Create a new history record with named parameters"""
        history = HistoryTable(
            content=content,
            role=role,
            events=events,
            dialog_id=dialog_id,
            token_usage=token_usage
        )
        async with async_session_getter() as session:
            session.add(history)
            await session.commit()
            await session.refresh(history)

    @classmethod
    async def select_history_from_time(cls, dialog_id: str, k: int) -> List[HistoryTable]:
        """Select recent k history records for a dialog"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.dialog_id == dialog_id
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
    async def get_dialog_history(cls, dialog_id: str):
        """Get all history records for a dialog ordered by time"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.dialog_id == dialog_id
            ).order_by(
                HistoryTable.create_time
            )
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def delete_history_by_dialog_id(cls, dialog_id: str):
        """Delete all history records for a dialog"""
        async with async_session_getter() as session:
            statement = delete(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def get_short_term_messages(cls, dialog_id, summary_last_time):
        """Get short term history messages"""
        async with async_session_getter() as session:
            statement = select(HistoryTable).where(
                HistoryTable.dialog_id == dialog_id,
                HistoryTable.create_time > summary_last_time
            ).order_by(
                HistoryTable.create_time
            )

            result = await session.exec(statement)
            return result.all()
