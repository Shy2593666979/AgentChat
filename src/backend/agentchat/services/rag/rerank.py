import asyncio
import json

import aiohttp
from agentchat.settings import app_settings, initialize_app_settings
from agentchat.schema.rerank import RerankResultModel


class Reranker:

    @classmethod
    async def request_rerank(cls, query, documents):
        if not documents:
            return []

        headers = {
            "Authorization": f"Bearer {app_settings.multi_models.rerank.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": app_settings.multi_models.rerank.model_name,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "return_documents": True,
                "top_n": app_settings.rag.retrival.get('top_k') * 2
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=app_settings.multi_models.rerank.base_url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['output']['results']
                else:
                    response.raise_for_status()

    @classmethod
    async def rerank_documents(cls, query, documents):
        final_documents = []
        original_documents = documents

        results = await cls.request_rerank(query, documents)

        for result in results:
            result['document'] = original_documents[result['index']]

            final_documents.append(RerankResultModel(query=query, content=result['document'],
                                                     score=result['relevance_score'], index=result['index']))
        return final_documents

if __name__ == "__main__":
    asyncio.run(initialize_app_settings("../../config.yaml"))

    asyncio.run(Reranker.rerank_documents(query="什么是文本排序模型", documents=[
            "文本排序模型广泛用于搜索引擎和推荐系统中，它们根据文本相关性对候选文本进行排序",
            "量子计算是计算科学的一个前沿领域",
            "预训练语言模型的发展给文本排序模型带来了新的进展"
        ]))