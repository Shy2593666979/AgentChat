from openai import AsyncOpenAI
from settings import app_settings


class AsyncChatClient(AsyncOpenAI):
    def __init__(self, base_url, api_key, model_name):
        self.model_name = model_name
        super().__init__(base_url=base_url, api_key=api_key)

    async def ainvoke(self, user_input, system_input: str = "你是一个有帮助的助手。"):
        response = await self.chat.completions.create(model=self.model_name,
                                                      messages=[
                                                          {"role": "system", "content": system_input},
                                                          {"role": "user", "content": user_input}])
        return response.choices[0].message.content


async_client = AsyncChatClient(base_url=app_settings.llm.get('base_url'),
                               api_key=app_settings.llm.get('api_key'),
                               model_name=app_settings.llm.get('model_name'))
