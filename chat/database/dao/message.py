from database.models.message import MessageDownTable, MessageLikeTable
from sqlmodel import Session
from sqlalchemy import select
from database import engine

class MessageLikeDao:

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


class MessageDownDao:

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
