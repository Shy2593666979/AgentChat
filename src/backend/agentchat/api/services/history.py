from typing import List
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agentchat.api.services.agent import AgentService
from agentchat.database.dao.conversation import ConversationDao
from agentchat.database.dao.history import HistoryDao
from agentchat.database.models.user import AdminUser
from agentchat.schemas.chunk import ChunkModel
from agentchat.services.rag.es_client import client as es_client
from agentchat.services.rag.vector_stores import milvus_client
from agentchat.utils.helpers import get_now_beijing_time

Assistant_Role = "assistant"
User_Role = "user"


class HistoryService:

    @classmethod
    async def create_history(
        cls,
        role: str,
        content: str,
        events: List[dict],
        conversation_id: str,
        token_usage: int = 0
    ):
        try:
            return await HistoryDao.create_history(
                role=role,
                content=content,
                events=events,
                conversation_id=conversation_id,
                token_usage=token_usage
            )
        except Exception as err:
            raise ValueError(f"Add history data appear error: {err}")

    @classmethod
    async def select_history(cls, conversation_id: str, top_k: int = 4) -> List[BaseMessage] | None:
        try:
            result = await HistoryDao.select_history_from_time(conversation_id, top_k)
            messages: List[BaseMessage] = []
            for data in result:
                if data.role == Assistant_Role:
                    messages.append(AIMessage(content=data.content))
                elif data.role == User_Role:
                    messages.append(HumanMessage(content=data.content))
            return messages
        except Exception as err:
            raise ValueError(f"Select history is appear error: {err}")

    @classmethod
    async def select_original_history_messages(cls, conversation_id: str, top_k: int = 10000):
        """直接选取全部的历史消息"""
        result = await HistoryDao.select_history_from_time(conversation_id, top_k)
        return result

    @classmethod
    async def enable_memory_select_history(cls, conversation_id: str, top_k: int = 10):
        pass

    @classmethod
    async def get_conversation_history(cls, conversation_id: str):
        try:
            results = await HistoryDao.get_conversation_history(conversation_id)
            conversation = await ConversationDao.select_conversation_by_id(conversation_id)
            agent = await AgentService.select_agent_by_id(conversation.agent_id) if conversation and conversation.agent_id else None
            histories = [res.to_dict() for res in results]
            # 旧会话尚未切换时，使用原智能体作为无身份记录消息的显示信息。
            if agent:
                identity = {
                    "type": "agent",
                    "data": {
                        "agent_id": agent["id"],
                        "name": agent["name"],
                        "logo_url": agent.get("logo_url", ""),
                    },
                }
                for history in histories:
                    events = history.get("events") or []
                    if history["role"] == Assistant_Role and not any(event.get("type") == "agent" for event in events):
                        history["events"] = [identity, *events]
            return histories
        except Exception as err:
            raise ValueError(f"Get conversation history is appear error: {err}")

    @classmethod
    async def save_es_documents(cls, index_name, content):
        chunk = ChunkModel(
            chunk_id=uuid4().hex,
            content=content,
            file_id="history_rag",
            knowledge_id=index_name,
            summary="history_rag",
            update_time=get_now_beijing_time(),
            file_name="history_rag",
        )

        chunks = [chunk]

        await es_client.index_documents(index_name, chunks)

    @classmethod
    async def save_milvus_documents(cls, collection_name, content):
        chunk = ChunkModel(
            chunk_id=uuid4().hex,
            content=content,
            file_id='history_rag',
            knowledge_id=collection_name,
            update_time=get_now_beijing_time(),
            summary="history_rag",
            file_name='history_rag'
        )
        chunks = [chunk]

        await milvus_client.insert(collection_name, chunks)

    @classmethod
    async def save_chat_history(cls, role, content, events, conversation_id, token_usage: int = 0, memory_enable: bool=False):
        return await cls.create_history(
            role=role,
            content=content,
            events=events,
            conversation_id=conversation_id,
            token_usage=token_usage
        )

        # 目前都已经改成使用Memory功能，历史记录只存数据库中
        # if memory_enable:
        #     documents = f"{role}: \n {content}"
        #     await cls.save_es_documents(conversation_id, documents)
        #     await cls.save_milvus_documents(conversation_id, documents)
        #
        #     # 更新对话窗口的最近使用时间
        #     await ConversationService.update_conversation_time(conversation_id=conversation_id)


    @classmethod
    async def get_short_term_messages(cls, conversation_id, user_id: str):
        """通过上次总结的时间来获取短期记忆, summary_last_time"""
        db_conversation = await ConversationDao.select_conversation_by_id(conversation_id)
        if db_conversation is None or user_id not in (AdminUser, db_conversation.user_id):
            raise ValueError(f"没有权限获取 {conversation_id} 的对话信息")

        short_term_messages = await HistoryDao.get_short_term_messages(conversation_id, db_conversation.summary_last_time)
        messages: List[BaseMessage] = []
        for msg in short_term_messages:
            if msg.role == Assistant_Role:
                messages.append(AIMessage(content=msg.content))
            elif msg.role == User_Role:
                messages.append(HumanMessage(content=msg.content))
        return messages
