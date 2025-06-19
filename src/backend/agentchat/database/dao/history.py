from agentchat.database.models.history import HistoryTable
from sqlmodel import Session
from sqlalchemy import select, delete
from agentchat.database import engine

class HistoryDao:

    @classmethod
    def _get_history_sql(cls, role: str, content: str, dialog_id: str):
        history = HistoryTable(content=content, role=role, dialog_id=dialog_id)
        return history

    @classmethod
    def create_history(cls, role: str, content: str, dialog_id: str):
        with Session(engine) as session:
            session.add(cls._get_history_sql(role, content, dialog_id))
            session.commit()

    @classmethod
    def select_history(cls, dialog_id: str, k: int):
        with Session(engine) as session:
            sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
            result = session.exec(sql).all()

            # 每次最多取当前会话的k条历史记录
            if len(result) > k:
                result = result[-k:]
            return result

    @classmethod
    def get_dialog_history(cls, dialog_id: str):
        with Session(engine) as session:
            sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id).order_by(HistoryTable.create_time)
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_history_by_dialog_id(cls, dialog_id: str):
        with Session(engine) as session:
            sql = delete(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
            session.exec(sql)
            session.commit()