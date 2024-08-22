from typing import List

from database.service import  HistoryService, DialogService, AgentService
from database.service import MessageDownService, MessageLikeService
from type.message import  Message
from loguru import  logger

class HistoryMessage:

    @classmethod
    def create_history(cls, role: str, content: str, dialogId: str):
        try:
            HistoryService.create_history(role, content, dialogId)
        except Exception as err:
            logger.error(f"add history data appear error: {err}")

    @classmethod
    def select_history(cls, dialogId: str, k: int = 6):
        try:
            result = HistoryService.select_history(dialogId, k)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"select history is appear error: {err}")

    @classmethod
    def get_dialog_history(cls, dialogId: str):
        try:
            result = HistoryService.get_dialog_history(dialogId)
            message_sql: List[Message] = []
            for data in result:
                message_sql.append(Message(content=data[0].content, role=data[0].role))
            return message_sql
        except Exception as err:
            logger.error(f"get dialog history is appear error: {err}")

class DialogChat:

    @classmethod
    def create_dialog(cls, name: str):
        try:
            dialogId = DialogService.create_dialog(name)
            return dialogId
        except Exception as err:
            logger.error(f"add dialog is appear error: {err}")

    @classmethod
    def select_dialog(cls, dialogId: str):
        try:
            data = DialogService.select_dialog(dialogId)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select dialog is appear error: {err}")

    @classmethod
    def get_list_dialog(cls):
        try:
            data = DialogService.get_list_dialog()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get list dialog is appear error: {err}")

class Agent:

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, parameter: str, type: str="openai", code: str="", isCustom: bool=True):
        try:
            agentId = AgentService.create_agent(name=name, description=description, logo=logo, parameter=parameter, type=type, code=code, isCustom=isCustom)
            return agentId
        except Exception as err:
            logger.error(f"create agent is appear error: {err}")

    @classmethod
    def get_agent(cls):
        try:
            data = AgentService.get_agent()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get agent is appear error: {err}")


    @classmethod
    def select_agent_by_type(cls, type: str):
        try:
            data = AgentService.select_agent_by_type(type)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by type is appear error: {err}")

    @classmethod
    def select_agent_by_custom(cls, isCustom):
        try:
            data = AgentService.select_agent_by_custom(isCustom=isCustom)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by custom is appear error: {err}")

    @classmethod
    def select_agent_by_name(cls, name: str):
        try:
            data = AgentService.select_agent_by_name(name)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"select agent by name is appear error: {err}")

    @classmethod
    def get_agent_by_name_type(cls, name: str, type: str="openai"):
        try:
            data = AgentService.get_agent_by_name_type(name=name, type=type)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get agent by name and type appear error: {err}")

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, code: str):
        try:
            data = AgentService.update_agent_by_id(id=id, name=name, logo=logo, description=description, parameter=parameter, code=code)
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"update agent by id appear error: {err}")

    @classmethod
    def delete_agent_by_id(cls, id: str):
        try:
            AgentService.delete_agent_by_id(id=id)
        except Exception as err:
            logger.error(f"delete agent by id appear: {err}")


class MessageLike:

    @classmethod
    def create_message_like(cls, userInput: str, agentOutput: str):
        try:
            MessageLikeService.create_message_like(userInput=userInput, agentOutput=agentOutput)

        except Exception as err:
            logger.error(f"create message like is appear error: {err}")

    @classmethod
    def get_message_like(cls):
        try:
            data = MessageLikeService.get_message_like()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get message like is appear error: {err}")

class MessageDown:

    @classmethod
    def create_message_down(cls, userInput: str, agentOutput: str):
        try:
            MessageDownService.create_message_down(userInput=userInput, agentOutput=agentOutput)

        except Exception as err:
            logger.error(f"create message down is appear error: {err}")

    @classmethod
    def get_message_down(cls):
        try:
            data = MessageDownService.get_message_down()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get message down is appear error: {err}")