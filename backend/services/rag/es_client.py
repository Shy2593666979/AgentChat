import json
from typing import List
from elasticsearch import AsyncElasticsearch
from schema.chunk import ChunkModel
from settings import app_settings
from loguru import logger

class AsyncESClient:
    def __init__(self):
        self.client = AsyncElasticsearch(hosts=app_settings.elasticsearch.get('hosts'))

    async def insert_documents(self, index_name, chunks: List[ChunkModel]):
        with open(app_settings.elasticsearch.get('index_config_path'), 'r') as f:
            index_config = json.loads(f.read())

        if not await self.client.indices.exists(index=index_name):

            try:
                await self.client.indices.create(index=index_name, body=index_config)
                logger.info(f'index name: {index_name} 创建成功')
            except Exception as e:
                logger.error(f"index name {index_name} error: {e}")
                raise ValueError(f"index create error")

        for chunk in chunks:
            await self.client.index(
                index=index_name,
                body=chunk.to_dict()
            )
            logger.info(f'chunk id: {chunk.chunk_id} 已存到索引中')

    async def index_documents(self, index_name, file_id, file_path, file_content, knowledge_id):
        chunks = await resolve_text(file_id, file_path, file_content, knowledge_id)
        await self.insert_documents(index_name, chunks)

    async def search_documents(self, query, index_name):
        with open(app_settings.elasticsearch.get('index_search_path'), 'r') as f:
            index_search = json.loads(f.read())

        try:
            response = await self.client.search(index=index_name, body=index_search)

