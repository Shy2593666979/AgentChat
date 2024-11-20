from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete
from typing import List
from database import engine
from database.models.llm import LLMTable
from datetime import datetime


class LLMDao:

    @classmethod
    def _create_llm(cls, model: str, base_url: str,
                    api_key: str, provider: str, user_id: str):
        llm = LLMTable(model=model, base_url=base_url,
                       api_key=api_key, provider=provider)
        return llm

    @classmethod
    def create_llm(cls, model: str, base_url: str,
                   api_key: str, provider: str, user_id: str):
        with Session(engine) as session:
            llm = cls._create_llm(model=model, base_url=base_url,
                                  api_key=api_key, provider=provider, user_id=user_id)
            session.add(llm)
            session.commit()

    @classmethod
    def delete_llm(cls, llm_id: str):
        with Session(engine) as session:
            sql = delete(LLMTable).where(LLMTable.llm_id == llm_id)
            session.exec(sql)
            session.commit()

    @classmethod
    def update_llm(cls, llm_id: str, base_url: str,
                   model: str, api_key: str, provider: str):
        with Session(engine) as session:
            update_values = {
                'create_time': datetime.utcnow()
            }
            if base_url:
                update_values['base_url'] = base_url
            if model:
                update_values['model'] = model
            if api_key:
                update_values['api_key'] = api_key
            if provider:
                update_values['provider'] = provider

            sql = update(LLMTable).where(LLMTable.llm_id == llm_id).values(**update_values)
            session.exec(sql)
            session.commit()

    @classmethod
    def get_llm_by_user(cls, user_id: str):
        with Session(engine) as session:
            sql = select(LLMTable).where(LLMTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_llm_by_id(cls, llm_id: str):
        with Session(engine) as session:
            sql = select(LLMTable).where(LLMTable.llm_id == llm_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    def get_all_llm(cls):
        with Session(engine) as session:
            sql = select(LLMTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_user_id_by_llm(cls, llm_id: str):
        with Session(engine) as session:
            sql = select(LLMTable)
            llm = session.exec(sql).first()
            return llm
