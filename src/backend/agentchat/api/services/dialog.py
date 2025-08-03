from agentchat.api.services.agent import AgentService
from agentchat.database.dao.dialog import DialogDao
from agentchat.database.dao.history import HistoryDao
from loguru import logger

from agentchat.database.models.user import AdminUser


class DialogService:

    @classmethod
    async def create_dialog(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        try:
            dialog = await DialogDao.create_dialog(name, agent_id, agent_type, user_id)
            return dialog.to_dict()
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
            dialog = await DialogDao.get_agent_by_dialog_id(dialog_id)
            return await AgentService.select_agent_by_id(dialog.agent_id)
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
            await HistoryDao.delete_history_by_dialog_id(dialog_id=dialog_id)
        except Exception as err:
            raise ValueError(f"Delete Dialog Appear Error: {err}")

    @classmethod
    async def verify_user_permission(cls, dialog_id, user_id):
        dialog = await DialogDao.get_agent_by_dialog_id(dialog_id)
        if user_id not in (AdminUser, dialog.user_id):
            raise ValueError(f"没有权限访问")

