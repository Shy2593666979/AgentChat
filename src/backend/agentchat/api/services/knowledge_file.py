from uuid import uuid4

from agentchat.database.dao.knowledge_file import KnowledgeFileDao
from agentchat.database.models.user import AdminUser
from agentchat.services.rag_handler import RagHandler


class KnowledgeFileService:
    @classmethod
    def parse_knowledge_file(cls):
        """使用 miner u 进行解析PDF，然后进行切割"""
        pass

    @classmethod
    async def get_knowledge_file(cls, knowledge_id):
        results = KnowledgeFileDao.select_knowledge_file(knowledge_id)
        return [res.to_dict() for res in results]

    @classmethod
    async def create_knowledge_file(cls, file_path, knowledge_id, user_id, oss_url):
        knowledge_file_id = uuid4().hex
        # 将上传的文件解析成chunks 放到ES 和 Milvus
        await RagHandler.index_es_documents(knowledge_id, knowledge_file_id, file_path, knowledge_id)
        await RagHandler.index_milvus_documents(knowledge_id, knowledge_file_id, file_path, knowledge_id)
        KnowledgeFileDao.create_knowledge_file(knowledge_file_id, file_path, knowledge_id, user_id, oss_url)

    @classmethod
    async def delete_knowledge_file(cls, knowledge_file_id):
        knowledge_file = await cls.select_knowledge_file_by_id(knowledge_file_id)
        await RagHandler.delete_documents_es_milvus(knowledge_file.file_id, knowledge_file.knowledge_id)

        KnowledgeFileDao.delete_knowledge_file(knowledge_file_id)

    @classmethod
    async def select_knowledge_file_by_id(cls, knowledge_file_id):
        knowledge_file = await KnowledgeFileDao.select_knowledge_file_by_id(knowledge_file_id)
        return knowledge_file

    @classmethod
    async def verify_user_permission(cls, knowledge_file_id, user_id):
        knowledge_file = await cls.select_knowledge_file_by_id(knowledge_file_id)
        if user_id not in (AdminUser, knowledge_file.user_id):
            raise ValueError("没有权限访问")