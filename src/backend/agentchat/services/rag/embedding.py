import asyncio
from typing import Union, List
from agentchat.core.models.manager import ModelManager
from agentchat.settings import app_settings

async def get_embedding(query: Union[str, List[str]]):
    embedding_client = ModelManager.get_embedding_openai_model()

    # 如果是字符串或长度小于等于10的列表，直接处理
    if isinstance(query, str) or (isinstance(query, list) and len(query) <= 10):
        responses = await embedding_client.embeddings.create(
            model=app_settings.multi_models.embedding.model_name,
            input=query,
            encoding_format="float"
        )

        if isinstance(query, str):
            return responses.data[0].embedding
        else:
            return [response.embedding for response in responses.data]

    # 处理超过10条的情况
    semaphore = asyncio.Semaphore(5)  # 限制并发数为5

    async def process_batch(batch):
        async with semaphore:
            responses = await embedding_client.embeddings.create(
                model=app_settings.multi_models.embedding.model_name,
                input=batch,
                encoding_format="float"
            )
            return [response.embedding for response in responses.data]

    # 将查询分成每组10条
    batches = [query[i:i + 10] for i in range(0, len(query), 10)]

    # 并发处理所有批次
    tasks = [process_batch(batch) for batch in batches]
    results = await asyncio.gather(*tasks)

    # 将所有结果合并
    return [embedding for batch_result in results for embedding in batch_result]


