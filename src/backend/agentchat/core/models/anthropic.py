from anthropic import Anthropic, AsyncAnthropic


class DeepAnthropic(Anthropic):
    def __init__(self, api_key, model, base_url, max_tokens=None):
        self.max_tokens = max_tokens or 1024
        self.model = model
        super().__init__(base_url=base_url, api_key=api_key)

    def invoke(self, messages, available_tools=None, max_tokens=None):
        response = self.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            tools=available_tools
        )
        return response

    async def invoke_stream(self, messages, available_tools=None, max_tokens=None):
        with self.messages.stream(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=messages,
                tools=available_tools
        ) as stream:
            for text in stream.text_stream:
                yield text


class DeepAsyncAnthropic(AsyncAnthropic):
    def __init__(self, api_key, model, base_url, max_tokens=None):
        self.max_tokens = max_tokens or 1024
        self.model = model
        super().__init__(base_url=base_url, api_key=api_key)

    async def ainvoke(self, messages, available_tools=None, max_tokens=None):
        response = await self.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            tools=available_tools
        )
        return response

    async def ainvoke_stream(self, messages, available_tools=None, max_tokens=None):
        with self.messages.stream(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=messages,
                tools=available_tools
        ) as stream:
            for text in stream.text_stream:
                yield text
