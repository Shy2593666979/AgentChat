from agentchat.database.models.message import MessageDownTable, MessageLikeTable
from sqlmodel import Session, select
from agentchat.database.session import session_getter

class MessageLikeDao:

    @classmethod
    def _get_message_like_sql(cls, user_input: str, agent_output: str):
        like = MessageLikeTable(user_input=user_input, agent_output=agent_output)
        return like

    @classmethod
    def create_message_like(cls, user_input: str, agent_output: str):
        with session_getter() as session:
            session.add(cls._get_message_like_sql(user_input, agent_output))
            session.commit()

    @classmethod
    def get_message_like(cls):
        with session_getter() as session:
            sql = select(MessageLikeTable)
            result = session.exec(sql).all()
            return result


class MessageDownDao:

    @classmethod
    def _get_message_down_sql(cls, user_input: str, agent_output: str):
        down = MessageDownTable(user_input=user_input, agent_output=agent_output)
        return down

    @classmethod
    def create_message_down(cls, user_input: str, agent_output: str):
        with session_getter() as session:
            session.add(cls._get_message_down_sql(user_input, agent_output))
            session.commit()

    @classmethod
    def get_message_down(cls):
        with session_getter() as session:
            sql = select(MessageDownTable)
            result = session.exec(sql).all()
            return result
