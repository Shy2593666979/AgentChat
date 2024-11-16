from database.models.dialog import DialogTable
from sqlmodel import Session
from sqlalchemy import select, update, desc, delete
from database import engine
from datetime import datetime

class DialogDao:

    @classmethod
    def _get_dialog_sql(cls, name: str, agent: str):
        dialog = DialogTable(name=name, agent=agent)
        return dialog

    @classmethod
    def create_dialog(cls, name, agent: str):
        with Session(engine) as session:
            dialog = cls._get_dialog_sql(name, agent)
            session.add(dialog)
            session.commit()
            return dialog.dialogId

    @classmethod
    def select_dialog(cls, dialogId: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialogId == dialogId)
            result = session.exec(sql).all()

            return result

    @classmethod
    def get_list_dialog(cls):
        with Session(engine) as session:
            sql = select(DialogTable).order_by(desc(DialogTable.createTime))
            result = session.exec(sql).all()

            return result

    @classmethod
    def get_agent_by_dialogId(cls, dialogId: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialogId == dialogId)
            result = session.exec(sql).all()
            return result

    @classmethod
    def update_dialog_time(cls, dialogId: str):
        with Session(engine) as session:
            sql = update(DialogTable).where(DialogTable.dialogId == dialogId).values(createTime=datetime.utcnow())
            session.exec(sql)
            session.commit()
            # dialog = session.exec(sql).one()
            #
            # dialog.createTime = datetime.utcnow()
            #
            # session.add(dialog)
            # session.commit()
            # session.refresh()

    @classmethod
    def delete_dialog_by_id(cls, dialogId: str):
        with Session(engine) as session:
            sql = delete(DialogTable).where(DialogTable.dialogId == dialogId)
            session.exec(sql)
            session.commit()

    @classmethod
    def check_dialog_iscustom(cls, dialogId: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialogId == dialogId)
            result = session.exec(sql).all()

            return result
