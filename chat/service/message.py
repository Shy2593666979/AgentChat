from database.dao.message import MessageDownDao, MessageLikeDao
from loguru import logger


class MessageLikeService:

    @classmethod
    def create_message_like(cls, userInput: str, agentOutput: str):
        try:
            MessageLikeDao.create_message_like(userInput=userInput, agentOutput=agentOutput)

        except Exception as err:
            logger.error(f"create message like is appear error: {err}")

    @classmethod
    def get_message_like(cls):
        try:
            data = MessageLikeDao.get_message_like()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get message like is appear error: {err}")

class MessageDownService:

    @classmethod
    def create_message_down(cls, userInput: str, agentOutput: str):
        try:
            MessageDownDao.create_message_down(userInput=userInput, agentOutput=agentOutput)

        except Exception as err:
            logger.error(f"create message down is appear error: {err}")

    @classmethod
    def get_message_down(cls):
        try:
            data = MessageDownDao.get_message_down()
            result = []
            for item in data:
                result.append(item[0])
            return result
        except Exception as err:
            logger.error(f"get message down is appear error: {err}")
