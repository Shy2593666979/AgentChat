from agentchat.database.dao.message import MessageDownDao, MessageLikeDao
from loguru import logger


class MessageLikeService:

    @classmethod
    def create_message_like(cls, user_input: str, agent_output: str):
        try:
            MessageLikeDao.create_message_like(user_input=user_input, agent_output=agent_output)

        except Exception as err:
            logger.error(f"create message like is appear error: {err}")

    @classmethod
    def get_message_like(cls):
        try:
            data = MessageLikeDao.get_message_like()
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"get message like is appear error: {err}")

class MessageDownService:

    @classmethod
    def create_message_down(cls, user_input: str, agent_output: str):
        try:
            MessageDownDao.create_message_down(user_input=user_input, agent_output=agent_output)

        except Exception as err:
            logger.error(f"create message down is appear error: {err}")

    @classmethod
    def get_message_down(cls):
        try:
            data = MessageDownDao.get_message_down()
            result = []
            for item in data:
                result.append(item)
            return result
        except Exception as err:
            logger.error(f"get message down is appear error: {err}")
