"""重排序超时/失败降级：外部重排服务变慢时不能拖死整条检索。

覆盖：
- 请求超时 -> 降级为混合检索原顺序，分数 1.0；
- 请求抛异常 -> 同样降级；
- 返回空结果 -> 降级；
- 正常返回 -> 按 relevance_score 排序；
- 超时默认值来自 rag.rerank_timeout。
"""
import asyncio
import time

from agentchat.schemas.common import Rag
from agentchat.services.rag.rerank import Reranker
from agentchat.settings import app_settings


def run(coro):
    return asyncio.run(coro)


def test_timeout_falls_back_to_hybrid_order(monkeypatch):
    monkeypatch.setattr(app_settings, "rag", Rag(enable_rerank=True, rerank_timeout=0.2))

    async def slow_request(query, documents):
        await asyncio.sleep(5)
        return [{"index": 0, "relevance_score": 0.9}]

    monkeypatch.setattr(Reranker, "request_rerank", staticmethod(slow_request))

    started = time.perf_counter()
    results = run(Reranker.rerank_documents("报销流程是什么？", ["文档A", "文档B", "文档C"]))
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0, f"超时后应立即降级，实际耗时 {elapsed:.2f}s"
    assert [doc.content for doc in results] == ["文档A", "文档B", "文档C"]
    assert [doc.score for doc in results] == [1.0, 1.0, 1.0]


def test_error_falls_back_to_hybrid_order(monkeypatch):
    monkeypatch.setattr(app_settings, "rag", Rag(enable_rerank=True, rerank_timeout=1.5))

    async def broken_request(query, documents):
        raise RuntimeError("upstream 503")

    monkeypatch.setattr(Reranker, "request_rerank", staticmethod(broken_request))

    results = run(Reranker.rerank_documents("问题", ["文档A", "文档B"]))
    assert [doc.content for doc in results] == ["文档A", "文档B"]


def test_empty_results_fall_back_to_hybrid_order(monkeypatch):
    monkeypatch.setattr(app_settings, "rag", Rag(enable_rerank=True, rerank_timeout=1.5))

    async def empty_request(query, documents):
        return []

    monkeypatch.setattr(Reranker, "request_rerank", staticmethod(empty_request))

    results = run(Reranker.rerank_documents("问题", ["文档A"]))
    assert [doc.content for doc in results] == ["文档A"]


def test_normal_scores_reorder_documents(monkeypatch):
    monkeypatch.setattr(app_settings, "rag", Rag(enable_rerank=True, rerank_timeout=1.5))

    async def fast_request(query, documents):
        return [
            {"index": 1, "relevance_score": 0.91},
            {"index": 0, "relevance_score": 0.12},
        ]

    monkeypatch.setattr(Reranker, "request_rerank", staticmethod(fast_request))

    results = run(Reranker.rerank_documents("问题", ["低分", "高分"]))
    assert [doc.content for doc in results] == ["高分", "低分"]
    assert [doc.score for doc in results] == [0.91, 0.12]


def test_no_documents_returns_empty(monkeypatch):
    monkeypatch.setattr(app_settings, "rag", Rag(enable_rerank=True, rerank_timeout=1.5))
    assert run(Reranker.rerank_documents("问题", [])) == []


def test_default_timeout_is_one_and_half_seconds():
    assert Rag().rerank_timeout == 1.5
