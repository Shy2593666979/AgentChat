from database.model import HistoryTable, DialogTable
from database.model import MessageDownTable, MessageLikeTable, ToolTable
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import select, and_
from config.service_config import  MYSQL_URL

engine = create_engine(MYSQL_URL)

class HistoryService:
    
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
            sql = select(HistoryTable).where(HistoryTable.dialogId == dialogId)
            result = session.exec(sql).all()
            return result

class DialogService:
    
    @classmethod
    def _get_dialog_sql(cls, name: str):
        dialog = DialogTable(name=name)
        return dialog
    
    @classmethod
    def create_dialog(cls, name):
        with Session(engine) as session:
            dialog = cls._get_dialog_sql(name)
            session.add(dialog)
            session.commit()
            return dialog.dialogId
    
    @classmethod
    def select_dialog(cls, dialogId: str):
        with Session(engine) as session:
            sql = select(DialogTable).where(DialogTable.dialogId == dialogId)
            result = session.exec(sql).all()
            
            return result

    @classmethod
    def get_list_dialog(cls):
        with Session(engine) as session:
            sql = select(DialogTable)
            result = session.exec(sql).all()

            return result

class ToolService:

    @classmethod
    def _get_tool_sql(cls, name: str, description: str, parameter: str, type: str):
        tool = ToolTable(name=name, description=description, parameter=parameter, type=type)
        return tool

    @classmethod
    def create_tool(cls, name: str, description: str, parameter: str, type: str):
        with Session(engine) as session:
            session.add(cls._get_tool_sql(name, description, parameter, type))
            session.commit()

    @classmethod
    def get_tool(cls):
        with Session(engine) as session:
            sql = select(ToolTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_tool_by_name(cls, name: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_tool_by_type(cls, type: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(ToolTable.type == type)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_tool_by_name_type(cls, name: str, type: str):
        with Session(engine) as session:
            sql = select(ToolTable).where(and_(ToolTable.name == name, ToolTable.type == type))
            result = session.exec(sql).all()
            return result


class MessageLikeService:

    @classmethod
    def _get_message_like_sql(cls, userInput: str, agentOutput: str):
        like = MessageLikeTable(userInput=userInput, agentOutput=agentOutput)
        return like

    @classmethod
    def create_message_like(cls, userInput: str, agentOutput: str):
        with Session(engine) as session:
            session.add(cls._get_message_like_sql(userInput, agentOutput))
            session.commit()

    @classmethod
    def get_message_like(cls):
        with Session(engine) as session:
            sql = select(MessageLikeTable)
            result = session.exec(sql).all()
            return result


class MessageDownService:

    @classmethod
    def _get_message_down_sql(cls, userInput: str, agentOutput: str):
        down = MessageDownTable(userInput=userInput, agentOutput=agentOutput)
        return down

    @classmethod
    def create_message_down(cls, userInput: str, agentOutput: str):
        with Session(engine) as session:
            session.add(cls._get_message_down_sql(userInput, agentOutput))
            session.commit()

    @classmethod
    def get_message_down(cls):
        with Session(engine) as session:
            sql = select(MessageDownTable)
            result = session.exec(sql).all()
            return result