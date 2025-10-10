from typing import List

from agentchat.database.models.history import HistoryTable
from sqlmodel import Session, select, delete
from agentchat.database.session import session_getter

class HistoryDao:

    @classmethod
    async def _get_history_sql(cls, role: str, content: str, events: List[dict], dialog_id: str):
        history = HistoryTable(content=content, role=role, events=events, dialog_id=dialog_id)
        return history

    @classmethod
    async def create_history(cls, role: str, content: str, events: List[dict], dialog_id: str):
        with session_getter() as session:
            session.add(await cls._get_history_sql(role, content, events, dialog_id))
            session.commit()

    @classmethod
    async def select_history_from_time(cls, dialog_id: str, k: int):
        with session_getter() as session:
            sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id).order_by(HistoryTable.create_time.desc())
            result = session.exec(sql).all()

            # 每次最多取当前会话的k条历史记录
            if len(result) > k:
                result = result[:k]
            # 保持消息的时间顺序（从旧到新）
            result.reverse()

            return result

    @classmethod
    async def get_dialog_history(cls, dialog_id: str):
        with session_getter() as session:
            sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id).order_by(HistoryTable.create_time)
            result = session.exec(sql).all()
            return result

    @classmethod
    async def delete_history_by_dialog_id(cls, dialog_id: str):
        with session_getter() as session:
            sql = delete(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
            session.exec(sql)
            session.commit()
