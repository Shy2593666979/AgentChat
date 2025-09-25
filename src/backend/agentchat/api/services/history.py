from typing import List
from uuid import uuid4

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from agentchat.api.services.dialog import DialogService
from agentchat.database.dao.history import HistoryDao
from agentchat.services.rag.es_client import client as es_client
from agentchat.services.rag.vector_db import milvus_client
from agentchat.schema.chunk import ChunkModel
from agentchat.utils.helpers import get_now_beijing_time

Assistant_Role = "assistant"
User_Role = "user"


class HistoryService:

    @classmethod
    async def create_history(cls, role: str, content: str, events: List[dict], dialog_id: str):
        try:
            await HistoryDao.create_history(role, content, events, dialog_id)
        except Exception as err:
            raise ValueError(f"Add history data appear error: {err}")

    @classmethod
    async def select_history(cls, dialog_id: str, top_k: int = 4) -> List[BaseMessage] | None:
        try:
            result = await HistoryDao.select_history_from_time(dialog_id, top_k)
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
    async def enable_memory_select_history(cls, dialog_id: str, top_k: int = 10):
        pass

    @classmethod
    async def get_dialog_history(cls, dialog_id: str):
        try:
            results = await HistoryDao.get_dialog_history(dialog_id)
            return [res.to_dict() for res in results]
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

    @classmethod
    async def save_chat_history(cls, role, content, events, dialog_id, embedding_enable: bool=False):
        await cls.create_history(role, content, events, dialog_id)

        # 目前都已经改成使用Memory功能，历史记录只存数据库中
        # if embedding_enable:
        #     documents = f"{role}: \n {content}"
        #     await cls.save_es_documents(dialog_id, documents)
        #     await cls.save_milvus_documents(dialog_id, documents)
        #
        #     # 更新对话窗口的最近使用时间
        #     await DialogService.update_dialog_time(dialog_id=dialog_id)
