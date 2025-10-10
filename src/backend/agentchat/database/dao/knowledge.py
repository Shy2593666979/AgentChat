from agentchat.database.session import session_getter
from datetime import datetime, timedelta
from agentchat.database.models.knowledge import KnowledgeTable
from sqlmodel import Session, select, delete, update, and_


class KnowledgeDao:

    @classmethod
    async def create_knowledge(cls, knowledge_name, knowledge_desc, user_id):
        with session_getter() as session:
            session.add(KnowledgeTable(name=knowledge_name, description=knowledge_desc,
                                       user_id=user_id))
            session.commit()

    @classmethod
    async def get_knowledge_by_user(cls, user_id):
        with session_getter() as session:
            sql = select(KnowledgeTable).where(KnowledgeTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_all_knowledge(cls):
        with session_getter() as session:
            sql = select(KnowledgeTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def delete_knowledge_by_id(cls, knowledge_id):
        with session_getter() as session:
            sql = delete(KnowledgeTable).where(KnowledgeTable.id == knowledge_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_knowledge_by_id(cls, knowledge_id, knowledge_desc, knowledge_name):
        with session_getter() as session:
            update_values = {}

            if knowledge_name:
                update_values['name'] = knowledge_name
            if knowledge_desc:
                update_values['description'] = knowledge_desc
            sql = update(KnowledgeTable).where(KnowledgeTable.id == knowledge_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    async def select_user_by_id(cls, knowledge_id):
        with session_getter() as session:
            sql = select(KnowledgeTable).where(KnowledgeTable.id == knowledge_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def get_knowledge_ids_from_name(cls, knowledges_name, user_id):
        with session_getter() as session:
            sql = select(KnowledgeTable).where(and_(KnowledgeTable.name.in_(knowledges_name),
                                                    KnowledgeTable.user_id == user_id))
            result = session.exec(sql)
            return result.all()