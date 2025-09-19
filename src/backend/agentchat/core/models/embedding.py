import asyncio
from typing import Union, List

from openai import AsyncOpenAI, OpenAI


class EmbeddingModel:
    def __init__(self, **kwargs):
        self.model = kwargs.get("model")
        self.api_key = kwargs.get("api_key")
        self.base_url = kwargs.get("base_url")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def embed(self, query: str):
        responses = self.client.embeddings.create(
            model=self.model,
            input=query,
            encoding_format="float")

        return responses.data[0].embedding

    # 异步处理更多的文本
    async def embed_async(self, query: Union[str, List[str]]):
        # 如果是字符串或长度小于等于10的列表，直接处理
        if isinstance(query, str) or (isinstance(query, list) and len(query) <= 10):
            responses = await self.client.embeddings.create(
                model=self.model,
                input=query,
                encoding_format="float")

            if isinstance(query, str):
                return responses.data[0].embedding
            else:
                return [response.embedding for response in responses.data]

        # 处理超过10条的情况
        semaphore = asyncio.Semaphore(5)  # 限制并发数为5

        async def process_batch(batch):
            async with semaphore:
                responses = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float")
                return [response.embedding for response in responses.data]

        # 将查询分成每组10条
        batches = [query[i:i + 10] for i in range(0, len(query), 10)]

        # 并发处理所有批次
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks)

        # 将所有结果合并
        return [embedding for batch_result in results for embedding in batch_result]
