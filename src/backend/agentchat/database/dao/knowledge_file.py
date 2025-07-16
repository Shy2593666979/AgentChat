from agentchat.database import engine
from agentchat.database.models.knowledge_file import KnowledgeFileTable
from sqlmodel import Session, select, delete


class KnowledgeFileDao:

    @classmethod
    async def create_knowledge_file(cls, knowledge_file_id, file_name, knowledge_id, user_id, oss_url):
        with Session(engine) as session:
            session.add(KnowledgeFileTable(file_name=file_name, knowledge_id=knowledge_id,
                                           user_id=user_id, oss_url=oss_url, id=knowledge_file_id))
            session.commit()

    @classmethod
    async def delete_knowledge_file(cls, knowledge_file_id):
        with Session(engine) as session:
            sql = delete(KnowledgeFileTable).where(KnowledgeFileTable.id == knowledge_file_id)
            session.exec(sql)

    @classmethod
    async def select_knowledge_file(cls, knowledge_id):
        with Session(engine) as session:
            sql = select(KnowledgeFileTable).where(KnowledgeFileTable.knowledge_id == knowledge_id)
            results = session.exec(sql).all()
            return results

    @classmethod
    async def select_knowledge_file_by_id(cls, knowledge_file_id):
        with Session(engine) as session:
            sql = select(KnowledgeFileTable).where(KnowledgeFileTable.id == knowledge_file_id)
            results = session.exec(sql).first()
            return results
