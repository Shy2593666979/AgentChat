from database.dao.knowledge_file import KnowledgeFileDao

class KnowledgeFileService:
    @classmethod
    def parse_knowledge_file(cls):
        """使用 miner u 进行解析PDF，然后进行切割"""
        pass

    @classmethod
    def get_knowledge_file(cls, knowledge_id):
        results = KnowledgeFileDao.select_knowledge_file(knowledge_id)
        result = []
        for data in results:
            result.append(data[0])
        return result

    @classmethod
    def create_knowledge_file(cls, file_name, knowledge_id, user_id, oss_url):
        KnowledgeFileDao.create_knowledge_file(file_name, knowledge_id, user_id, oss_url)

    @classmethod
    def delete_knowledge_file(cls, knowledge_id):
        KnowledgeFileDao.delete_knowledge_file(knowledge_id)
        