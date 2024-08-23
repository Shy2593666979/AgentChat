from database.model import HistoryTable, DialogTable
from database.model import MessageDownTable, MessageLikeTable, AgentTable
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import select, and_
from config.service_config import  MYSQL_URL
from chat.utils.helpers import delete_img

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
    def _get_dialog_sql(cls, name: str, agent: str):
        dialog = DialogTable(name=name, agent=agent)
        return dialog
    
    @classmethod
    def create_dialog(cls, name, agent: str):
        with Session(engine) as session:
            dialog = cls._get_dialog_sql(name, agent)
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

class AgentService:

    @classmethod
    def _get_agent_sql(cls, name: str, description: str, logo: str, parameter: str, type: str, code: str, isCustom: bool):
        agent = AgentTable(name=name, description=description, logo=logo, parameter=parameter, type=type, code=code, isCustom=isCustom)
        return agent

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, parameter: str, type: str, code: str, isCustom: bool):
        with Session(engine) as session:
            session.add(cls._get_agent_sql(name, description, logo, parameter, type, code, isCustom))
            session.commit()

    @classmethod
    def get_agent(cls):
        with Session(engine) as session:
            sql = select(AgentTable)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_type(cls, type: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.type == type)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_custom(cls, isCustom: bool):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.isCustom == isCustom)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_agent_by_name_type(cls, name: str, type: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.type == type))
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_agent_by_id(cls, id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            agent = session.exec(sql).one()

            # 删除agent的logo地址
            delete_img(logo=agent.logo)

            session.delete(agent)
            session.commit()

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, type: str, code: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            agent = session.exec(sql).one()

            if name is not None:
                agent.name = name
            if description is not None:
                agent.description = description
            if parameter is not None:
                agent.parameter = parameter
            if type is not None:
                agent.type = type
            if code is not None:
                agent.code = code
            if logo is not None:
                # 删除agent的logo地址
                delete_img(logo=logo)
                agent.logo = logo

            session.add(agent)
            session.commit()
            session.refresh()

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