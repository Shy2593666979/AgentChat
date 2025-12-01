from uuid import uuid4

from loguru import logger
from agentchat.database.dao.knowledge_file import KnowledgeFileDao
from agentchat.database.models.knowledge_file import Status
from agentchat.database.models.user import AdminUser
from agentchat.services.rag.parser import doc_parser
from agentchat.services.rag_handler import RagHandler
from agentchat.settings import app_settings

class KnowledgeFileService:
    @classmethod
    def parse_knowledge_file(cls):
        """使用 miner u 进行解析PDF，然后进行切割"""
        pass

    @classmethod
    async def get_knowledge_file(cls, knowledge_id):
        results = await KnowledgeFileDao.select_knowledge_file(knowledge_id)
        return [res.to_dict() for res in results]

    @classmethod
    async def create_knowledge_file(cls, file_name, file_path, knowledge_id, user_id, oss_url, file_size_bytes):
        knowledge_file_id = uuid4().hex
        await KnowledgeFileDao.create_knowledge_file(knowledge_file_id, file_name, knowledge_id, user_id, oss_url, file_size_bytes)
        try:
            # 解析状态改成 进行中
            await cls.update_parsing_status(knowledge_file_id, Status.process)
            # 针对不同的文件类型进行解析
            chunks = await doc_parser.parse_doc_into_chunks(knowledge_file_id, file_path, knowledge_id)

            # 将上传的文件解析成chunks 放到ES 和 Milvus
            await RagHandler.index_milvus_documents(knowledge_id, chunks)
            if app_settings.rag.enable_elasticsearch:
                await RagHandler.index_es_documents(knowledge_id, chunks)
            # 解析状态改为 成功
            await cls.update_parsing_status(knowledge_file_id, Status.success)
        except Exception as err:
            # 解析状态改为 失败
            logger.info(f"Create Knowledge File Error: {err}")
            await cls.update_parsing_status(knowledge_file_id, Status.fail)
            raise ValueError(f"Create Knowledge File Error: {err}")

    @classmethod
    async def delete_knowledge_file(cls, knowledge_file_id):
        knowledge_file = await cls.select_knowledge_file_by_id(knowledge_file_id)
        await RagHandler.delete_documents_es_milvus(knowledge_file.id, knowledge_file.knowledge_id)

        await KnowledgeFileDao.delete_knowledge_file(knowledge_file_id)

    @classmethod
    async def select_knowledge_file_by_id(cls, knowledge_file_id):
        knowledge_file = await KnowledgeFileDao.select_knowledge_file_by_id(knowledge_file_id)
        return knowledge_file

    @classmethod
    async def verify_user_permission(cls, knowledge_file_id, user_id):
        knowledge_file = await cls.select_knowledge_file_by_id(knowledge_file_id)
        if user_id not in (AdminUser, knowledge_file.user_id):
            raise ValueError("没有权限访问")

    @classmethod
    async def update_parsing_status(cls, knowledge_file_id, status):
        return await KnowledgeFileDao.update_parsing_status(knowledge_file_id, status)