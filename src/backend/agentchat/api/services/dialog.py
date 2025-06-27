from agentchat.database.dao.dialog import DialogDao
from agentchat.database.dao.history import HistoryDao
from loguru import logger


class DialogService:

    @classmethod
    async def create_dialog(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        try:
            await DialogDao.create_dialog(name, agent_id, agent_type, user_id)
        except Exception as err:
            raise ValueError(f"Add Dialog Appear Error: {err}")

    @classmethod
    async def select_dialog(cls, dialog_id: str):
        try:
            results = await DialogDao.select_dialog(dialog_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Select Dialog Appear Error: {err}")

    @classmethod
    async def get_list_dialog(cls, user_id: str):
        try:
            results = await DialogDao.get_dialog_by_user(user_id=user_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get List Dialog Appear Error: {err}")

    @classmethod
    async def get_agent_by_dialog_id(cls, dialog_id: str):
        try:
            results = await DialogDao.get_agent_by_dialog_id(dialog_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Select Dialog Appear Error: {err}")

    @classmethod
    async def update_dialog_time(cls, dialog_id: str):
        try:
            await DialogDao.update_dialog_time(dialog_id=dialog_id)
        except Exception as err:
            raise ValueError(f"Update Dialog Create Time Appear Error: {err}")

    @classmethod
    async def delete_dialog(cls, dialog_id: str):
        try:
            await DialogDao.delete_dialog_by_id(dialog_id=dialog_id)
            HistoryDao.delete_history_by_dialog_id(dialog_id=dialog_id)
        except Exception as err:
            raise ValueError(f"Delete Dialog Appear Error: {err}")

    @classmethod
    async def check_dialog_iscustom(cls, dialog_id: str):
        try:
            result = await DialogDao.check_dialog_iscustom(dialog_id=dialog_id)
            for data in result:
                if data[0].is_custom:
                    return True
            return False
        except Exception as err:
            raise ValueError(f"Check Dialog Custom Appear Error: {err}")
