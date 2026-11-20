import asyncio
import json

import aiohttp
from loguru import logger

from agentchat.settings import app_settings
from agentchat.schemas.rerank import RerankResultModel


class Reranker:
    """重排序接口适配。

    - DashScope：请求体为 input/parameters，结果在 output.results；
    - SiliconFlow（Cohere 风格）：请求体为 query/documents，结果在 results，
      响应字段统一为 index / relevance_score，因此下游解析逻辑可以共用。

    外部重排服务可能排队变慢，这里用 rag.rerank_timeout 限制总耗时；
    超时后降级为混合检索的原顺序（分数 1.0），避免整条检索被拖死。
    """

    @classmethod
    def _is_cohere_style(cls, base_url: str) -> bool:
        return "siliconflow" in (base_url or "").lower()

    @classmethod
    def _top_n(cls, documents) -> int:
        top_k = app_settings.rag.retrival.get('top_k') or 5
        return max(1, min(top_k * 2, len(documents)))

    @classmethod
    async def request_rerank(cls, query, documents):
        if not documents:
            return []

        base_url = app_settings.multi_models.rerank.base_url
        headers = {
            "Authorization": f"Bearer {app_settings.multi_models.rerank.api_key}",
            "Content-Type": "application/json"
        }

        if cls._is_cohere_style(base_url):
            payload = {
                "model": app_settings.multi_models.rerank.model_name,
                "query": query,
                "documents": documents,
                "top_n": cls._top_n(documents),
                "return_documents": True,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url=base_url, headers=headers, data=json.dumps(payload)) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["results"]
                    response.raise_for_status()

        payload = {
            "model": app_settings.multi_models.rerank.model_name,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "return_documents": True,
                "top_n": cls._top_n(documents)
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=base_url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['output']['results']
                else:
                    response.raise_for_status()

    @classmethod
    def _rerank_timeout(cls) -> float:
        timeout = getattr(app_settings.rag, "rerank_timeout", None)
        try:
            timeout = float(timeout)
        except (TypeError, ValueError):
            timeout = 0
        return timeout if timeout > 0 else 1.5

    @classmethod
    def _fallback(cls, query, documents):
        """重排不可用或超时时，保持混合检索的原顺序，分数置 1.0 以避免被阈值误杀。"""
        return [RerankResultModel(query=query, content=content, score=1.0, index=index)
                for index, content in enumerate(documents)]

    @classmethod
    async def rerank_documents(cls, query, documents):
        if not documents:
            return []

        timeout = cls._rerank_timeout()
        try:
            results = await asyncio.wait_for(cls.request_rerank(query, documents), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"rerank 超时（>{timeout:.1f}s），降级为混合检索顺序")
            return cls._fallback(query, documents)
        except Exception as err:
            logger.warning(f"rerank 调用失败（{err}），降级为混合检索顺序")
            return cls._fallback(query, documents)

        if not results:
            logger.warning("rerank 返回空结果，降级为混合检索顺序")
            return cls._fallback(query, documents)

        final_documents = []
        original_documents = documents

        for result in results:
            result['document'] = original_documents[result['index']]

            final_documents.append(RerankResultModel(query=query, content=result['document'],
                                                     score=result['relevance_score'], index=result['index']))
        return final_documents

if __name__ == "__main__":
    asyncio.run(Reranker.rerank_documents(query="什么是文本排序模型", documents=[
            "文本排序模型广泛用于搜索引擎和推荐系统中，它们根据文本相关性对候选文本进行排序",
            "量子计算是计算科学的一个前沿领域",
            "预训练语言模型的发展给文本排序模型带来了新的进展"
        ]))
