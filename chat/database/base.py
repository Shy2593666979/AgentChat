from typing import List

from database.service import  HistoryService, DialogService, ToolService
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
            result = DialogService.select_dialog(dialogId)
            return result
        except Exception as err:
            logger.error(f"select dialog is appear error: {err}")

    @classmethod
    def get_list_dialog(cls):
        try:
            result = DialogService.get_list_dialog()
            return result
        except Exception as err:
            logger.error(f"get list dialog is appear error: {err}")

class Tool:

    @classmethod
    def create_tool(cls, name: str, description: str, parameter: str, type: str="openai"):
        try:
            toolId = ToolService.create_tool(name=name, description=description, parameter=parameter, type=type)
            return toolId
        except Exception as err:
            logger.error(f"create tool is appear error: {err}")

    @classmethod
    def get_tool(cls):
        try:
            result = ToolService.get_tool()
            return result
        except Exception as err:
            logger.error(f"get tool is appear error: {err}")

    @classmethod
    def select_tool_by_type(cls, type: str):
        try:
            result = ToolService.select_tool_by_type(type)
            return result
        except Exception as err:
            logger.error(f"select tool by type is appear error: {err}")

    @classmethod
    def select_tool_by_name(cls, name: str):
        try:
            result = ToolService.select_tool_by_name(name)
            return result
        except Exception as err:
            logger.error(f"select tool by name is appear error: {err}")

    @classmethod
    def get_tool_by_name_type(cls, name: str, type: str="openai"):
        try:
            result = ToolService.get_tool_by_name_type(name=name, type=type)
            return result
        except Exception as err:
            logger.error(f"get tool by name and type appear error: {err}")

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
            result = MessageLikeService.get_message_like()
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
            result = MessageDownService.get_message_down()
            return result
        except Exception as err:
            logger.error(f"get message down is appear error: {err}")