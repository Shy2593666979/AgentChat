from database.dao.dialog import DialogDao
from database.dao.history import HistoryDao
from loguru import logger


class DialogService:

    @classmethod
    def create_dialog(cls, name: str, agent: str):
        try:
            dialogId = DialogDao.create_dialog(name, agent)
            return dialogId
        except Exception as err:
            logger.error(f"add dialog is appear error: {err}")

    @classmethod
    def select_dialog(cls, dialogId: str):
        try:
            data = DialogDao.select_dialog(dialogId)
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
    def get_agent_by_dialogId(cls, dialogId: str):
        try:
            data = DialogDao.get_agent_by_dialogId(dialogId)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select dialog is appear error: {err}")

    @classmethod
    def update_dialog_time(cls, dialogId: str):
        try:
            DialogDao.update_dialog_time(dialogId=dialogId)
        except Exception as err:
            logger.error(f"update dialog create time appear error: {err}")

    @classmethod
    def delete_dialog(cls, dialogId: str):
        try:
            DialogDao.delete_dialog_by_id(dialogId=dialogId)
            HistoryDao.delete_history_by_dialogId(dialogId=dialogId)
        except Exception as err:
            logger.error(f"delete dialog appear error: {err}")

    @classmethod
    def check_dialog_iscustom(cls, dialogId: str):
        try:
            result = DialogDao.check_dialog_iscustom(dialogId=dialogId)
            for data in result:
                if data[0].isCustom:
                    return True
            return False
        except Exception as err:
            logger.error(f"check dialog is Custom appear error: {err}")
