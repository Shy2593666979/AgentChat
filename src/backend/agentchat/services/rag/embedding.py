import asyncio
from typing import Union, List

from openai import AsyncOpenAI
from agentchat.settings import app_settings, initialize_app_settings

embedding_model = app_settings.multi_models.embedding.model_name
embedding_client = AsyncOpenAI(base_url=app_settings.multi_models.embedding.base_url,
                               api_key=app_settings.multi_models.embedding.api_key)

async def get_embedding(query: Union[str, List[str]]):
    # 如果是字符串或长度小于等于10的列表，直接处理
    if isinstance(query, str) or (isinstance(query, list) and len(query) <= 10):
        responses = await embedding_client.embeddings.create(
            model=embedding_model,
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
            responses = await embedding_client.embeddings.create(
                model=embedding_model,
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


if __name__ == "__main__":
    asyncio.run(initialize_app_settings("../../config.yaml"))

    asyncio.run(get_embedding(["大模型"]))
