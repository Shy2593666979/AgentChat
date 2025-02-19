from database import engine
from database.models.knowledge_file import KnowledgeFileTable
from sqlmodel import Session
from sqlalchemy import select, delete

class KnowledgeFileDao:

    @classmethod
    def create_knowledge_file(cls, file_name, knowledge_id, user_id, oss_url):
        with Session(engine) as session:
            session.add(KnowledgeFileTable(file_name=file_name, knowledge_id=knowledge_id,
                                           user_id=user_id, oss_url=oss_url))
            session.commit()

    @classmethod
    def delete_knowledge_file(cls, knowledge_file_id):
        with Session(engine) as session:
            sql = delete(KnowledgeFileTable).where(KnowledgeFileTable.id == knowledge_file_id)
            session.exec(sql)

    @classmethod
    def select_knowledge_file(cls, knowledge_id):
        with Session(engine) as session:
            sql = select(KnowledgeFileTable).where(KnowledgeFileTable.knowledge_id == knowledge_id)
            results = session.exec(sql).all()
            return results

