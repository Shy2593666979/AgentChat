from agentchat.api.services.chat import ChatService
from agentchat.api.services.dialog import DialogService


class ChatClient:
    def __init__(self, **kwargs):
        self.chat_service = None
        self.dialog_id = kwargs.get('dialog_id')
        self.chat_service = None

        self.init_chat_service()

    def init_chat_service(self):
        agent = DialogService.get_agent_by_dialog_id(dialog_id=self.dialog_id)
        self.chat_service = ChatService(dialog_id=self.dialog_id, **agent)

    async def send_response(self, user_input: str):
        async for one in self.chat_service.run(user_input):
            yield one

