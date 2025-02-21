from openai import AsyncOpenAI


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