from typing import List
from database.dao.history import HistoryDao
from type.message import Message
from loguru import logger


class HistoryService:

    @classmethod
    def create_history(cls, role: str, content: str, dialog_id: str):
        try:
            HistoryDao.create_history(role, content, dialog_id)
        except Exception as err:
            logger.error(f"add history data appear error: {err}")

    @classmethod
    def select_history(cls, dialog_id: str, k: int = 6):
        try:
            result = HistoryDao.select_history(dialog_id, k)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"select history is appear error: {err}")

    @classmethod
    def get_dialog_history(cls, dialog_id: str):
        try:
            result = HistoryDao.get_dialog_history(dialog_id)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"get dialog history is appear error: {err}")
