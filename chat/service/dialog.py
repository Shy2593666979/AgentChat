from database.dao.dialog import DialogDao
from database.dao.history import HistoryDao
from loguru import logger


class DialogService:

    @classmethod
    def create_dialog(cls, name: str, agent: str):
        try:
            dialog_id = DialogDao.create_dialog(name, agent)
            return dialog_id
        except Exception as err:
            logger.error(f"add dialog is appear error: {err}")

    @classmethod
    def select_dialog(cls, dialog_id: str):
        try:
            data = DialogDao.select_dialog(dialog_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select dialog is appear error: {err}")

    @classmethod
    def get_list_dialog(cls):
        try:
            data = DialogDao.get_list_dialog()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get list dialog is appear error: {err}")

    @classmethod
    def get_agent_by_dialog_id(cls, dialog_id: str):
        try:
            data = DialogDao.get_agent_by_dialog_id(dialog_id)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select dialog is appear error: {err}")

    @classmethod
    def update_dialog_time(cls, dialog_id: str):
        try:
            DialogDao.update_dialog_time(dialog_id=dialog_id)
        except Exception as err:
            logger.error(f"update dialog create time appear error: {err}")

    @classmethod
    def delete_dialog(cls, dialog_id: str):
        try:
            DialogDao.delete_dialog_by_id(dialog_id=dialog_id)
            HistoryDao.delete_history_by_dialog_id(dialog_id=dialog_id)
        except Exception as err:
            logger.error(f"delete dialog appear error: {err}")

    @classmethod
    def check_dialog_iscustom(cls, dialog_id: str):
        try:
            result = DialogDao.check_dialog_iscustom(dialog_id=dialog_id)
            for data in result:
                if data[0].is_custom:
                    return True
            return False
        except Exception as err:
            logger.error(f"check dialog is Custom appear error: {err}")
