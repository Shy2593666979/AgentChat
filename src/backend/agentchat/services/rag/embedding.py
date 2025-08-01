from openai import AsyncOpenAI
from agentchat.settings import app_settings

embedding_model = app_settings.embedding.get('model_name')
embedding_client = AsyncOpenAI(base_url=app_settings.embedding.get('base_url'), api_key=app_settings.embedding.get('api_key'))


async def get_embedding(query):
    response = await embedding_client.embeddings.create(
        model=embedding_model,
        input=query,
        encoding_format="float")

    response = response.model_dump_json()
    return response['data'][0]['embedding']

