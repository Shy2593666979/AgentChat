from uuid import uuid4

from database.dao.knowledge_file import KnowledgeFileDao
from services.rag_handler import RagHandler


class KnowledgeFileService:
    @classmethod
    def parse_knowledge_file(cls):
        """使用 miner u 进行解析PDF，然后进行切割"""
        pass

    @classmethod
    async def get_knowledge_file(cls, knowledge_id):
        results = KnowledgeFileDao.select_knowledge_file(knowledge_id)
        result = []
        for data in results:
            result.append(data[0])
        return result

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
        knowledge_file = await KnowledgeFileDao.select_knowledge_file_by_id(knowledge_file_id)[0][0]
        return knowledge_file