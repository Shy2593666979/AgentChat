from sqlmodel import select, and_, update, delete, or_

from agentchat.database import SystemUser
from agentchat.database.session import session_getter, async_session_getter
from agentchat.database.models.llm import LLMTable


class LLMDao:

    @classmethod
    async def create_llm(
        cls,
        model: str,
        base_url: str,
        llm_type: str,
        api_key: str,
        provider: str,
        user_id: str
    ):
        with session_getter() as session:
            llm = LLMTable(
                model=model,
                base_url=base_url,
                api_key=api_key,
                provider=provider,
                user_id=user_id,
                llm_type=llm_type
            )
            session.add(llm)
            session.commit()

    @classmethod
    async def delete_llm(cls, llm_id: str):
        with session_getter() as session:
            sql = delete(LLMTable).where(LLMTable.llm_id == llm_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def update_llm(
        cls,
        llm_id: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        provider: str = None,
        llm_type: str = None
    ):
        update_values = {
            k: v for k, v in {
                "model": model,
                "base_url": base_url,
                "api_key": api_key,
                "provider": provider,
                "llm_type": llm_type
            }.items() if v is not None
        }

        if not update_values:
            return

        with session_getter() as session:
            sql = (
                update(LLMTable)
                .where(LLMTable.llm_id == llm_id)
                .values(**update_values)
            )
            session.exec(sql)
            session.commit()

    @classmethod
    async def get_llm_by_user(cls, user_id: str):
        with session_getter() as session:
            return session.exec(
                select(LLMTable).where(LLMTable.user_id == user_id)
            ).all()

    @classmethod
    async def get_llm_by_id(cls, llm_id: str):
        with session_getter() as session:
            return session.exec(
                select(LLMTable).where(LLMTable.llm_id == llm_id)
            ).first()

    @classmethod
    async def get_all_llm(cls):
        with session_getter() as session:
            return session.exec(select(LLMTable)).all()

    @classmethod
    async def get_user_id_by_llm(cls, llm_id: str):
        with session_getter() as session:
            return session.exec(
                select(LLMTable).where(LLMTable.llm_id == llm_id)
            ).first()

    @classmethod
    async def get_llm_by_type(cls, llm_type: str):
        with session_getter() as session:
            return session.exec(
                select(LLMTable).where(LLMTable.llm_type == llm_type)
            ).all()

    @classmethod
    async def get_llm_id_from_name(cls, llm_name: str, user_id: str):
        with session_getter() as session:
            return session.exec(
                select(LLMTable).where(
                    and_(
                        LLMTable.model == llm_name,
                        LLMTable.user_id == user_id
                    )
                )
            ).first()

    @classmethod
    async def search_llms_by_name(cls, user_id, llm_name):
        async with async_session_getter() as session:
            statement = select(LLMTable).where(
                or_(
                    LLMTable.user_id == user_id,
                    LLMTable.user_id == SystemUser
                ),
                LLMTable.model.ilike(f"%{llm_name}%")
            )

            result = await session.exec(statement)
            return result.all()
