from database import engine
from datetime import datetime, timedelta
from database.models.knowledge import KnowledgeTable
from sqlmodel import Session, select, delete, update


class KnowledgeDao:

    @classmethod
    def create_knowledge(cls, knowledge_name, knowledge_desc, user_id, oss_object_name):
        with Session(engine) as session:
            session.add(KnowledgeTable(name=knowledge_name, description=knowledge_desc,
                                       user_id=user_id, oss_object_name=oss_object_name))
            session.commit()

    @classmethod
    def get_knowledge_by_user(cls, user_id):
        with Session(engine) as session:
            sql = select(KnowledgeTable).where(KnowledgeTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_knowledge_by_id(cls, knowledge_id):
        with Session(engine) as session:
            sql = delete(KnowledgeTable).where(KnowledgeTable.id == knowledge_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_knowledge_by_id(cls, knowledge_id, knowledge_desc, knowledge_name):
        with Session(engine) as session:
            update_values = {'create_time': datetime.utcnow() + timedelta(hours=8)}

            if knowledge_name:
                update_values['name'] = knowledge_name
            if knowledge_desc:
                update_values['description'] = knowledge_desc
            sql = update(KnowledgeTable).where(KnowledgeTable.id == knowledge_id).values(**update_values)
            session.exec(sql)
            session.commit()