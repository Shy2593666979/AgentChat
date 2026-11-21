"""向量化调用的超时与熔断：外部 embedding 变慢时不能拖死整条检索。

覆盖：
- 单次调用超时后抛错并打开熔断；
- 熔断期内直接快速失败，不再请求外部服务；
- 快速失败（连接错误）在预算内重试一次；
- 正常调用返回向量；
- 超过 10 条时分批调用，结果按顺序合并。
"""
import asyncio
import time
from types import SimpleNamespace

import pytest

from agentchat.schemas.common import Rag
from agentchat.services.rag import embedding as embedding_module
from agentchat.settings import app_settings


def run(coro):
    return asyncio.run(coro)


def fake_response(count=1):
    return SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1, 0.2]) for _ in range(count)]
    )


def patch_client(monkeypatch, create):
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    monkeypatch.setattr(
        embedding_module.ModelManager, "get_embedding_openai_model", staticmethod(lambda: client)
    )
    monkeypatch.setattr(
        app_settings, "multi_models", SimpleNamespace(embedding=SimpleNamespace(model_name="fake-embedding"))
    )
    monkeypatch.setattr(app_settings, "rag", Rag(embedding_timeout=0.2, embedding_cooldown=5.0))
    monkeypatch.setattr(embedding_module, "_unavailable_until", 0.0)


def test_slow_embedding_times_out_and_opens_breaker(monkeypatch):
    async def slow_create(**kwargs):
        await asyncio.sleep(5)
        return fake_response()

    patch_client(monkeypatch, slow_create)

    started = time.perf_counter()
    with pytest.raises(asyncio.TimeoutError):
        run(embedding_module.get_embedding("问题"))
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"应在预算内失败，实际 {elapsed:.2f}s"
    assert embedding_module._breaker_open(), "超时后应该打开熔断"


def test_open_breaker_fails_fast_without_calling_client(monkeypatch):
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        return fake_response()

    patch_client(monkeypatch, create)
    monkeypatch.setattr(embedding_module, "_unavailable_until", time.monotonic() + 10)

    started = time.perf_counter()
    with pytest.raises(RuntimeError):
        run(embedding_module.get_embedding("问题"))
    elapsed = time.perf_counter() - started

    assert elapsed < 0.05, f"熔断期应快速失败，实际 {elapsed:.3f}s"
    assert calls == [], "熔断期不应再请求外部服务"


def test_fast_error_retries_once_within_budget(monkeypatch):
    calls = []

    async def flaky_create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise ConnectionError("connection reset")
        return fake_response()

    patch_client(monkeypatch, flaky_create)

    result = run(embedding_module.get_embedding("问题"))
    assert result == [0.1, 0.2]
    assert len(calls) == 2, "连接错误应在预算内重试一次"


def test_normal_call_returns_embedding(monkeypatch):
    async def create(**kwargs):
        return fake_response()

    patch_client(monkeypatch, create)
    assert run(embedding_module.get_embedding("问题")) == [0.1, 0.2]


def test_batch_over_ten_items(monkeypatch):
    calls = []

    async def create(**kwargs):
        calls.append(kwargs["input"])
        return fake_response(len(kwargs["input"]))

    patch_client(monkeypatch, create)

    result = run(embedding_module.get_embedding([f"文档{i}" for i in range(15)]))
    assert len(result) == 15
    assert len(calls) == 2, "15 条应分成两批调用"
