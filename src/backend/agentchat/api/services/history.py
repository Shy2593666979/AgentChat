from typing import List
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from agentchat.api.services.dialog import DialogService
from agentchat.database.dao.history import HistoryDao
from agentchat.schema.message import Message
from loguru import logger
from agentchat.services.rag.es_client import client as es_client
from agentchat.services.rag.milvus_client import client as milvus_client
from agentchat.schema.chunk import ChunkModel
from agentchat.utils.helpers import get_now_beijing_time

Assistant_Role = "assistant"
User_Role = "user"


class HistoryService:

    @classmethod
    async def create_history(cls, role: str, content: str, dialog_id: str):
        try:
            await HistoryDao.create_history(role, content, dialog_id)
        except Exception as err:
            raise ValueError(f"Add history data appear error: {err}")

    @classmethod
    async def select_history(cls, dialog_id: str, top_k: int = 5) -> List[BaseMessage] | None:
        try:
            result = await HistoryDao.select_history(dialog_id, top_k)
            messages: List[BaseMessage] = []
            for data in result:
                if data[0].role == Assistant_Role:
                    messages.append(AIMessage(content=data[0].content))
                elif data[0].role == User_Role:
                    messages.append(AIMessage(content=data[0].content))
            return messages
        except Exception as err:
            raise ValueError(f"Select history is appear error: {err}")

    @classmethod
    async def use_embedding_select_history(cls, dialog_id: str, top_k: int = 10):
        pass

    @classmethod
    async def get_dialog_history(cls, dialog_id: str):
        try:
            results = await HistoryDao.get_dialog_history(dialog_id)
            return [res[0].to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get dialog history is appear error: {err}")

    @classmethod
    async def save_es_documents(cls, index_name, content):
        chunks = [ChunkModel(chunk_id=uuid4().hex,
                             content=content,
                             file_id='history_rag',
                             knowledge_id=index_name,
                             summary="history_rag",
                             update_time=get_now_beijing_time(),
                             file_name='history_rag')]

        await es_client.index_documents(index_name, chunks)

    @classmethod
    async def save_milvus_documents(cls, collection_name, content):
        chunks = [ChunkModel(chunk_id=uuid4().hex,
                             content=content,
                             file_id='history_rag',
                             knowledge_id=collection_name,
                             update_time=get_now_beijing_time(),
                             summary="history_rag",
                             file_name='history_rag')]

        await milvus_client.insert(collection_name, chunks)

    # 历史记录都存milvus 和 es一份，开启RAG召回历史记录
    @classmethod
    async def save_chat_history(cls, role, content, knowledge_id):
        documents = f"{role}: \n {content}"

        await cls.create_history(role, content, knowledge_id)

        await cls.save_es_documents(knowledge_id, documents)
        await cls.save_milvus_documents(knowledge_id, documents)

        # 更新对话窗口的最近使用时间
        await DialogService.update_dialog_time(dialog_id=knowledge_id)
