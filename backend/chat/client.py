from service.chat import ChatService
from service.dialog import DialogService
from type.message import Message
from typing import List
from service.history import HistoryService


class ChatClient:
    def __init__(self, **kwargs):
        self.chat_service = None
        self.user_input = kwargs.get('user_input')
        self.dialog_id = kwargs.get('dialog_id')
        self.chat_service = None
        self.embedding = None

        self.init_chat_service()

    def init_chat_service(self):
        agent = DialogService.get_agent_by_dialog_id(dialog_id=self.dialog_id)
        self.chat_service = ChatService(**agent)

    def get_history_message(self, dialog_id: str, top_k: int = 5):
        messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k)
        result = []
        for message in messages:
            result.append(message)
        return result

    # 使用RAG检索的方式将最近10条数据按照相关性排序，取top_k个


    async def send_response(self, user_input: str, history_message: List[Message]):
        history = ''
        for message in history_message:
            history += message.to_str()

        async for one in self.chat_service.run(user_input, history):
            yield one



