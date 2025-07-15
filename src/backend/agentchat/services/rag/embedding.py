import asyncio
from typing import Union, List

from openai import AsyncOpenAI
from agentchat.settings import app_settings, initialize_app_settings

embedding_model = app_settings.embedding.get('model_name')
embedding_client = AsyncOpenAI(base_url=app_settings.embedding.get('base_url'),
                               api_key=app_settings.embedding.get('api_key'))

async def get_embedding(query: Union[str, List[str]]):
    responses = await embedding_client.embeddings.create(
        model=embedding_model,
        input=query,
        encoding_format="float")

    if isinstance(query, str):
        return responses.data[0].embedding
    else:
        return [response.embedding for response in responses.data]


if __name__ == "__main__":
    asyncio.run(initialize_app_settings("../../config.yaml"))

    asyncio.run(get_embedding(["你好啊", "你是谁？"]))
