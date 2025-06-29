from agentchat.database.models.dialog import DialogTable
from sqlmodel import Session
from sqlalchemy import select, update, desc, delete
from agentchat.database import engine
from datetime import datetime

class DialogDao:

    @classmethod
    async def _get_dialog_sql(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        dialog = DialogTable(name=name, agent_id=agent_id, agent_type=agent_type, user_id=user_id)
        return dialog

    @classmethod
    async def create_dialog(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        with Session(engine) as session:
            dialog = await cls._get_dialog_sql(name, agent_id, agent_type, user_id)
            session.add(dialog)
            session.commit()

    @classmethod
    async def select_dialog(cls, dialog_id: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = session.exec(sql).all()

            return result

    @classmethod
    async def get_dialog_by_user(cls, user_id: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.user_id == user_id).order_by(desc(DialogTable.create_time))
            result = session.exec(sql).all()

            return result

    @classmethod
    async def get_agent_by_dialog_id(cls, dialog_id: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    async def update_dialog_time(cls, dialog_id: str):
        with Session(engine) as session:
            sql = update(DialogTable).where(DialogTable.dialog_id == dialog_id).values(create_time=datetime.utcnow())
            session.exec(sql)
            session.commit()

    @classmethod
    async def delete_dialog_by_id(cls, dialog_id: str):
        with Session(engine) as session:
            sql = delete(DialogTable).where(DialogTable.dialog_id == dialog_id)
            session.exec(sql)
            session.commit()

    @classmethod
    async def check_dialog_iscustom(cls, dialog_id: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = session.exec(sql).first()

            return result
