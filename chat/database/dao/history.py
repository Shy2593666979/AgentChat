from database.models.history import HistoryTable
from sqlmodel import Session
from sqlalchemy import select, delete
from database import engine

class HistoryDao:

    @classmethod
    def _get_history_sql(cls, role: str, content: str, dialogId: str):
        history = HistoryTable(content=content, role=role, dialogId=dialogId)
        return history

    @classmethod
    def create_history(cls, role: str, content: str, dialogId: str):
        with Session(engine) as session:
            session.add(cls._get_history_sql(role, content, dialogId))
            session.commit()

    @classmethod
    def select_history(cls, dialogId: str, k: int):
        with Session(engine) as session:
            sql = select(HistoryTable).where(HistoryTable.dialogId == dialogId)
            result = session.exec(sql).all()

            # 每次最多取当前会话的k条历史记录
            if len(result) > k:
                result = result[-k:]
            return result

    @classmethod
    def get_dialog_history(cls, dialogId: str):
        with Session(engine) as session:
            sql = select(HistoryTable).where(HistoryTable.dialogId == dialogId).order_by(HistoryTable.createTime)
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_history_by_dialogId(cls, dialogId: str):
        with Session(engine) as session:
            sql = delete(HistoryTable).where(HistoryTable.dialogId == dialogId)
            session.exec(sql)
            session.commit()