from typing import List
from uuid import uuid4


from database.dao.history import HistoryDao
from schema.message import Message
from loguru import logger
from services.rag.es_client import client as es_client
from services.rag.milvus_client import client as milvus_client
from schema.chunk import ChunkModel
from utils.helpers import get_now_beijing_time

class HistoryService:

    @classmethod
    def create_history(cls, role: str, content: str, dialog_id: str):
        try:
            HistoryDao.create_history(role, content, dialog_id)
        except Exception as err:
            logger.error(f"add history data appear error: {err}")

    @classmethod
    def select_history(cls, dialog_id: str, top_k: int = 5):
        try:
            result = HistoryDao.select_history(dialog_id, top_k)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"select history is appear error: {err}")

    @classmethod
    def get_dialog_history(cls, dialog_id: str):
        try:
            result = HistoryDao.get_dialog_history(dialog_id)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"get dialog history is appear error: {err}")

    @classmethod
    async def save_es_documents(cls, index_name, content):
        chunks = [ChunkModel(chunk_id=uuid4().hex,
                             content=content,
                             file_id='history_rag',
                             knowledge_id=index_name,
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
                             file_name='history_rag')]

        await milvus_client.insert(collection_name, chunks)

    # 历史记录都存milvus 和 es一份，开启RAG召回历史记录
    @classmethod
    async def save_chat_history(cls, role, knowledge_id, content):
        documents = f"{role}: \n {content}"

        cls.create_history(role, content, knowledge_id)

        await cls.save_es_documents(knowledge_id, documents)
        await cls.save_milvus_documents(knowledge_id, documents)


