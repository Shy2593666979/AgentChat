from sqlmodel import Session, select, and_, update, desc, delete
from agentchat.database.session import session_getter
from agentchat.database.models.llm import LLMTable
from datetime import datetime


class LLMDao:

    @classmethod
    async def _create_llm(cls, model: str, base_url: str, llm_type: str,
                          api_key: str, provider: str, user_id: str):
        llm = LLMTable(model=model, base_url=base_url,
                       api_key=api_key, provider=provider, user_id=user_id)
        return llm

    @classmethod
    async def create_llm(cls, model: str, base_url: str, llm_type: str,
                         api_key: str, provider: str, user_id: str):
        with session_getter() as session:
            llm = await cls._create_llm(model=model, base_url=base_url, llm_type=llm_type,
                                        api_key=api_key, provider=provider, user_id=user_id)
            session.add(llm)
            session.commit()

    @classmethod
    async def delete_llm(cls, llm_id: str):
        with session_getter() as session:
            sql = delete(LLMTable).where(LLMTable.llm_id == llm_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_llm(cls, llm_id: str, base_url: str, llm_type: str,
                         model: str, api_key: str, provider: str):
        with session_getter() as session:
            update_values = {}
            if base_url:
                update_values['base_url'] = base_url
            if model:
                update_values['model'] = model
            if api_key:
                update_values['api_key'] = api_key
            if provider:
                update_values['provider'] = provider
            if llm_type:
                update_values['llm_type'] = llm_type

            sql = update(LLMTable).where(LLMTable.llm_id == llm_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    async def get_llm_by_user(cls, user_id: str):
        with session_getter() as session:
            sql = select(LLMTable).where(LLMTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_llm_by_id(cls, llm_id: str):
        with session_getter() as session:
            sql = select(LLMTable).where(LLMTable.llm_id == llm_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def get_all_llm(cls):
        with session_getter() as session:
            sql = select(LLMTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_user_id_by_llm(cls, llm_id: str):
        with session_getter() as session:
            sql = select(LLMTable).where(LLMTable.llm_id == llm_id)
            llm = session.exec(sql).first()
            return llm

    @classmethod
    async def get_llm_by_type(cls, llm_type: str):
        with session_getter() as session:
            sql = select(LLMTable).where(LLMTable.llm_type == llm_type)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def get_llm_id_from_name(cls, llm_name, user_id):
        with session_getter() as session:
            sql = select(LLMTable).where(and_(LLMTable.model == llm_name,
                                              LLMTable.user_id == user_id))
            result = session.exec(sql)
            return result.first()
