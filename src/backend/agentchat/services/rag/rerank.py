import json

import aiohttp
from agentchat.settings import app_settings
from agentchat.schema.rerank import RerankResultModel


class Reranker:

    @classmethod
    async def request_rerank(cls, query, documents):
        headers = {
            "Authorization": f"Bearer {app_settings.rerank.get('api_key')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": app_settings.rerank.get('model_name'),
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "return_documents": True,
                "top_n": app_settings.rerank.get('top_n')
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=app_settings.rerank.get('endpoint'), headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['result']
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

