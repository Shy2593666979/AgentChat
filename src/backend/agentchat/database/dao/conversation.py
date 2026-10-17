from datetime import datetime, timedelta, timezone

from sqlmodel import Session, delete, desc, select, update

from agentchat.database.models.agent import AgentTable
from agentchat.database.models.conversation import ConversationTable
from agentchat.database.models.history import HistoryTable
from agentchat.database.session import async_session_getter


class ConversationDao:

    @classmethod
    async def create_conversation(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        """Create a new conversation with named parameters"""
        conversation = ConversationTable(
            name=name,
            agent_id=agent_id,
            agent_type=agent_type,
            user_id=user_id
        )
        async with async_session_getter() as session:
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)  # 确保获取数据库生成的字段
            return conversation

    @classmethod
    async def select_conversation_by_id(cls, conversation_id: str) -> ConversationTable:
        """Select conversation by conversation_id"""
        async with async_session_getter() as session:
            statement = select(ConversationTable).where(ConversationTable.conversation_id == conversation_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def get_conversation_by_user(cls, user_id: str):
        """Get all conversations for a user ordered by create time"""
        async with async_session_getter() as session:
            statement = select(ConversationTable).where(
                ConversationTable.user_id == user_id
            ).order_by(desc(ConversationTable.create_time))
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_by_conversation_id(cls, conversation_id: str):
        """Get agent information by conversation_id"""
        async with async_session_getter() as session:
            statement = select(ConversationTable).where(ConversationTable.conversation_id == conversation_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def update_conversation_time(cls, conversation_id: str):
        """更新会话活动时间，保留原创建时间。"""
        async with async_session_getter() as session:
            statement = update(ConversationTable).where(
                ConversationTable.conversation_id == conversation_id
            ).values(update_time=datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None))
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def delete_conversation_by_id(cls, conversation_id: str):
        """Delete conversation by conversation_id"""
        async with async_session_getter() as session:
            statement = delete(ConversationTable).where(ConversationTable.conversation_id == conversation_id)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def check_conversation_iscustom(cls, conversation_id: str):
        """Check if conversation is custom by conversation_id"""
        async with async_session_getter() as session:
            statement = select(ConversationTable).where(ConversationTable.conversation_id == conversation_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def detach_agent(cls, agent_id: str):
        """删除智能体时保留会话与历史，仅清空当前选择。"""
        async with async_session_getter() as session:
            agent = await session.get(AgentTable, agent_id)
            conversations = (await session.exec(select(ConversationTable).where(ConversationTable.agent_id == agent_id))).all()
            for conversation in conversations:
                await cls._backfill_reply_agents(session, conversation.conversation_id, agent)
            statement = update(ConversationTable).where(ConversationTable.agent_id == agent_id).values(agent_id="")
            await session.exec(statement)
            await session.commit()

    @staticmethod
    async def _backfill_reply_agents(session, conversation_id, agent):
        """为旧消息补充原智能体身份，切换后仍展示实际回复者。"""
        if agent is None:
            return
        histories = (await session.exec(select(HistoryTable).where(
            HistoryTable.conversation_id == conversation_id, HistoryTable.role == "assistant"))).all()
        identity = {
            "type": "agent",
            "data": {
                "agent_id": agent.id,
                "name": agent.name,
                "logo_url": agent.logo_url or "",
            },
        }
        for history in histories:
            events = history.events or []
            if not any(event.get("type") == "agent" for event in events):
                history.events = [identity, *events]
                session.add(history)

    @classmethod
    async def switch_agent(cls, conversation_id: str, agent_id: str):
        """只改变后续回复所选智能体，保留会话 ID、标题、摘要与消息。"""
        async with async_session_getter() as session:
            conversation = await session.get(ConversationTable, conversation_id)
            if conversation is None:
                raise ValueError("会话不存在")
            if conversation.agent_id != agent_id:
                previous = await session.get(AgentTable, conversation.agent_id) if conversation.agent_id else None
                await cls._backfill_reply_agents(session, conversation_id, previous)
                conversation.agent_id = agent_id
                conversation.agent_type = "Agent"
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)
            return conversation

    @classmethod
    async def update_title_if_unchanged(cls, conversation_id: str, expected_name: str, title: str):
        """异步生成只更新标题，不改变会话活动顺序。"""
        async with async_session_getter() as session:
            statement = update(ConversationTable).where(
                ConversationTable.conversation_id == conversation_id, ConversationTable.name == expected_name
            ).values(name=title, update_time=ConversationTable.update_time)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def update_conversation_summary(cls, conversation_id, summary, summary_last_time):
        """Update conversation summary"""
        async with async_session_getter() as session:
            db_conversation = await session.get(ConversationTable, conversation_id)

            if summary:
                db_conversation.summary = summary
            if summary_last_time:
                db_conversation.summary_last_time = summary_last_time

            await session.commit()
            await session.refresh(db_conversation)
