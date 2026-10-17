"""简易配置及本地基础设施检查，不调用外部模型或修改现有数据。"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from agentchat.schemas.common import LocalStorageConfig
from agentchat.services.memory_cache import MemoryCacheConnection
from agentchat.settings import app_settings, init_app_settings, load_settings


def write_config(tmp_path, data):
    path = tmp_path / "config.simple.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_key_only_defaults_and_no_shared_credentials(tmp_path):
    settings = load_settings(
        write_config(
            tmp_path,
            {
                "model": {
                    "api_key": "test-only",
                },
            },
        )
    )
    assert settings.simple_mode
    assert settings.database == {
        "url": "sqlite:///data/agentchat.db",
    }
    assert settings.redis["endpoint"] is None
    assert settings.storage.mode == "local"
    assert settings.multi_models.chat_model.api_key == "test-only"
    assert settings.multi_models.tool_call_model.model_name == "qwen-plus"
    assert settings.multi_models.reasoning_model.api_key == "test-only"
    assert settings.multi_models.embedding.model_name == "text-embedding-v4"
    assert settings.tools.tavily["api_key"] == ""
    assert settings.wechat_config == settings.langfuse == {}


def test_shipped_template_preserves_full_structure_and_inherits_models(tmp_path):
    template = Path(__file__).parents[1] / "agentchat/config.simple.yaml"
    data = yaml.safe_load(template.read_text(encoding="utf-8"))
    assert "model" not in data
    assert data["storage"]["mode"] == "local"
    with pytest.raises(ValueError):
        load_settings(template)
    data["multi_models"]["chat_model"]["api_key"] = "test-only"
    settings = load_settings(write_config(tmp_path, data))
    assert settings.simple_mode
    assert settings.multi_models.tool_call_model.api_key == "test-only"
    assert settings.multi_models.embedding.api_key == "test-only"
    assert settings.multi_models.embedding.base_url == settings.multi_models.chat_model.base_url
    assert settings.storage.local.path == "data/uploads"
    assert settings.rag.split["chunk_size"] == 500


def test_nested_overrides_and_legacy_mysql(tmp_path):
    settings = load_settings(
        write_config(
            tmp_path,
            {
                "model": {
                    "api_key": "test-only",
                    "model_name": "custom",
                },
                "rag": {
                    "split": {
                        "chunk_size": 900,
                    },
                },
                "server": {
                    "port": 9001,
                },
                "multi_models": {
                    "tool_call_model": {
                        "model_name": "tools",
                    },
                },
            },
        )
    )
    assert settings.rag.split == {
        "chunk_size": 900,
        "overlap_size": 100,
    }
    assert settings.multi_models.tool_call_model.api_key == "test-only"
    assert settings.multi_models.tool_call_model.model_name == "tools"
    assert settings.storage.local.base_url == "http://127.0.0.1:9001/uploads/"
    legacy = load_settings(
        write_config(
            tmp_path,
            {
                "mysql": {
                    "endpoint": "mysql://u:p@localhost/example",
                },
            },
        )
    )
    assert legacy.database == {}
    assert legacy.mysql["endpoint"].startswith("mysql://")
    full = load_settings(Path(__file__).parents[1] / "agentchat/config.yaml")
    assert not full.simple_mode
    assert full.storage.mode == "minio"


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {
            "model": {},
        },
        {
            "model": {
                "api_key": " ",
            },
        },
        {
            "model": "invalid",
        },
    ],
)
def test_invalid_simple_config_fails(tmp_path, data):
    with pytest.raises(ValueError):
        load_settings(write_config(tmp_path, data))


def test_environment_selection_updates_shared_object_atomically(tmp_path, monkeypatch):
    previous = {
        key: getattr(app_settings, key)
        for key in app_settings.__fields__
    }
    identity = id(app_settings)
    try:
        monkeypatch.setenv(
            "AGENTCHAT_CONFIG",
            str(
                write_config(
                    tmp_path,
                    {
                        "model": {
                            "api_key": "test-only",
                        },
                    },
                )
            ),
        )
        asyncio.run(init_app_settings())
        assert id(app_settings) == identity
        assert app_settings.simple_mode
        invalid = write_config(
            tmp_path,
            {
                "model": {
                    "api_key": "",
                },
            },
        )
        with pytest.raises(ValueError):
            asyncio.run(init_app_settings(invalid))
        assert app_settings.multi_models.chat_model.api_key == "test-only"
    finally:
        for key, value in previous.items():
            setattr(app_settings, key, value)


def test_memory_cache_expiration_atomic_creation_and_hashes():
    cache = MemoryCacheConnection()
    with patch("agentchat.services.memory_cache.monotonic", return_value=100):
        assert cache.setnx("token", b"first")
        assert not cache.setnx("token", b"second")
        cache.expire("token", 5)
        assert (
            cache.hset(
                "hash",
                mapping={
                    "a": "one",
                },
            )
            == 1
        )
        assert cache.hset("hash", "a", "two") == 0
        assert cache.hgetall("hash") == {
            "a": "two",
        }
        assert cache.incr("count") == 1
        assert cache.incr("count") == 2
        cache.setex("long", 10000, "retained")
        cache.close()
    with patch("agentchat.services.memory_cache.monotonic", return_value=106):
        assert cache.get("token") is None
        assert cache.get("long") == "retained"
        assert cache.delete("hash") == 1


def test_local_file_roundtrip_url_and_path_escape(tmp_path):
    # 本地模块经包导入时需要一个有效的存储选择。
    previous = app_settings.storage
    from agentchat.schemas.common import StorageConfig
    app_settings.storage = StorageConfig(
        mode="local",
        local={
            "path": str(tmp_path),
        },
    )
    try:
        from agentchat.services.storage.local import LocalStorageClient
        client = LocalStorageClient(LocalStorageConfig(path=str(tmp_path), base_url="http://localhost/uploads/"))
        client.upload_file("files/test.txt", "测试内容")
        assert client.list_files_in_folder("files") == ["files/test.txt"]
        url = client.sign_url_for_get("files/test.txt")
        client.download_file(url, tmp_path / "copy.txt")
        assert (tmp_path / "copy.txt").read_text(encoding="utf-8") == "测试内容"
        client.download_file("uploads/files/test.txt", tmp_path / "copy2.txt")
        client.upload_local_file("files/copy.txt", tmp_path / "copy2.txt")
        assert len(client.list_files_in_folder("files")) == 2
        with pytest.raises(ValueError):
            client.upload_file("../escape.txt", b"invalid")
        with pytest.raises(ValueError):
            client.upload_file("%2e%2e/escape.txt", b"invalid")
    finally:
        app_settings.storage = previous


def test_mcp_sessions_without_redis():
    from agentchat.mcp_proxy.session.manager import SessionManager
    from agentchat.mcp_proxy.session.models import ClientCapabilities, ClientInfo

    async def check():
        manager = SessionManager()
        session = await manager.create_session("test", "dev", ClientInfo(name="test", version="1"), ClientCapabilities())
        assert await manager.exists_session(session.session_id)
        assert (await manager.touch_session(session.session_id)).session_id == session.session_id
        await manager.delete_session(session.session_id)
        assert await manager.get_session(session.session_id) is None
        assert not await manager.exists_session(session.session_id)
    asyncio.run(check())


def test_fresh_app_start_login_upload_and_restart(tmp_path):
    path = write_config(
        tmp_path,
        {
            "whitelist_paths": ["/api/v1/mcp/*", "/mcp/*"],
            "model": {
                "api_key": "test-only-not-a-real-key",
            },
            "database": {
                "url": "sqlite:///" + (tmp_path / "app.db").as_posix(),
            },
            "storage": {
                "local": {
                    "path": str(tmp_path / "uploads"),
                },
            },
        },
    )
    script = '''
from fastapi.testclient import TestClient
from agentchat.main import app
with TestClient(app) as client:
    assert client.get("/health").json() == {"status": "OK"}
    assert app.state.session_manager._redis is None
    from agentchat.services.redis import redis_client
    redis_client.set("check", {"value": "memory"})
    assert redis_client.get("check") == {"value": "memory"}
    registered = client.post("/api/v1/user/register", json={"user_name": "simple_test", "user_email": "simple@example.test", "user_password": "local-test"})
    assert registered.status_code == 200, registered.text
    login = client.post("/api/v1/user/login", json={"user_name": "simple_test", "user_password": "local-test"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    uploaded = client.post("/api/v1/upload", files={"file": ("test.txt", b"local upload", "text/plain")}, headers={"Authorization": "Bearer " + token})
    assert uploaded.status_code == 200, uploaded.text
    url = uploaded.json()["data"]
    assert "/uploads/files/" in url, uploaded.text
    from urllib.parse import urlparse
    result = client.get(urlparse(url).path)
    assert result.status_code == 200 and result.content == b"local upload", result.text
    from agentchat.database import engine, AgentTable
    from sqlmodel import Session, select
    with Session(engine) as session:
        agent = session.exec(select(AgentTable).where(AgentTable.user_id == login.json()["data"]["user_id"])).first()
        assert agent is not None
        agent_id = agent.id
    from ag_ui.core import Event
    from pydantic import TypeAdapter
    validator = TypeAdapter(Event)
    protocol_headers = {"Authorization": "Bearer " + token, "X-AgentChat-Protocol": "ag-ui/1.0"}
    def read_events(response):
        assert response.status_code == 200, response.text
        import json
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        for event in events:
            validator.validate_python(event)
        assert events[0]["type"] == "RUN_STARTED"
        assert events[-1]["type"] in ("RUN_FINISHED", "RUN_ERROR")
        return events

    # 只替换模型执行，保留真实接口、鉴权、数据库保存和 Token 回调。
    import agentchat.api.v1.completion as conversation_module
    class FakeConversation:
        def __init__(self, config): pass
        async def init_agent(self): pass
        def stop_streaming_callback(self): pass
        async def astream(self, messages):
            yield {"type": "response_chunk", "data": {"chunk": "mock answer"}}
            from langchain_core.messages import AIMessage
            from langchain_core.outputs import LLMResult, ChatGeneration
            from agentchat.core.callbacks.usage_metadata import UsageMetadataCallbackHandler
            UsageMetadataCallbackHandler().on_llm_end(LLMResult(generations=[[ChatGeneration(message=AIMessage(content="mock answer", response_metadata={"model_name": "mock"}, usage_metadata={"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}))]]))
    conversation_module.GeneralAgent = FakeConversation
    conversation_module.ConversationService.queue_conversation_title = lambda *args: None
    async def no_summary(*args, **kwargs): pass
    conversation_module.ConversationService.update_conversation_summary = no_summary
    created = client.post("/api/v1/conversation", json={"agent_id": agent_id}, headers=protocol_headers)
    conversation_id = created.json()["data"]["conversation_id"]
    events = read_events(client.post("/api/v1/completion", json={"conversation_id": conversation_id, "agent_id": agent_id, "user_input": "test question"}, headers=protocol_headers))
    assert events[-1]["type"] == "RUN_FINISHED"
    listing = client.get("/api/v1/conversation/list", headers=protocol_headers).json()["data"]
    assert next(row for row in listing if row["conversation_id"] == conversation_id)["total_tokens"] == 7

    import agentchat.api.v1.mars as mars_module
    class FakeMars:
        def __init__(self, config): pass
        async def init_mars_agent(self): pass
        async def ainvoke_stream(self, messages):
            yield {"type": "response_chunk", "data": "mock mars"}
    mars_module.MarsAgent = FakeMars
    assert read_events(client.post("/api/v1/mars/example", json={"example_id": 2}, headers=protocol_headers))[-1]["type"] == "RUN_FINISHED"
    # Mars 的记忆检索和写入异常不能中断主对话，且必须保留用户隔离。
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    mars_memory = SimpleNamespace(search=AsyncMock(side_effect=RuntimeError("invalid_api_key")), add=AsyncMock())
    mars_module.memory_client = mars_memory
    mars_events = read_events(client.post("/api/v1/mars/chat", json={"user_input": "hello"}, headers=protocol_headers))
    assert mars_events[-1]["type"] == "RUN_FINISHED"
    assert any(event["type"] == "TEXT_MESSAGE_CONTENT" and event["delta"] == "mock mars" for event in mars_events)
    mars_memory.add.assert_not_awaited()
    assert mars_memory.search.call_args.kwargs["user_id"] == login.json()["data"]["user_id"]
    mars_memory.search.side_effect = None
    mars_memory.search.return_value = {"results": []}
    mars_memory.add.side_effect = RuntimeError("memory write failed")
    assert read_events(client.post("/api/v1/mars/chat", json={"user_input": "hello"}, headers=protocol_headers))[-1]["type"] == "RUN_FINISHED"
    assert mars_memory.add.call_args.kwargs["user_id"] == login.json()["data"]["user_id"]

    import agentchat.api.v1.lingseek as workspace_module
    class FakeWorkspace:
        def __init__(self, user_id): pass
        async def generate_guide_prompt(self, *args):
            yield {"event": "generate_guide_prompt", "data": {"chunk": "mock guide"}}
    workspace_module.LingSeekAgent = FakeWorkspace
    assert read_events(client.post("/api/v1/workspace/lingseek/guide_prompt", json={"query": "test"}, headers=protocol_headers))[-1]["type"] == "RUN_FINISHED"

    import agentchat.api.v1.register_mcp_completion as mcp_module
    class FakeMcp:
        async def astream(self, *args, **kwargs):
            yield {"type": "text", "content": "confirm"}
            yield {"type": "interrupt", "event": {"interrupt_id": "approval", "status": False, "allowed_decisions": ["approve", "reject"]}}
        async def astream_resume(self, *args, **kwargs):
            yield {"type": "text", "content": "registered"}
    mcp_module.abstract_mcp_agent = FakeMcp()
    interrupted = read_events(client.post("/api/v1/mcp/register/completion", json={"task_id": "test-mcp", "query": "test"}, headers=protocol_headers))
    assert interrupted[-1]["outcome"]["type"] == "interrupt"
    assert client.post("/api/v1/mcp/register/completion/hitl/approve", json={"task_id": "test-mcp", "interrupt_id": "stale"}, headers=protocol_headers).status_code == 409
    approved = read_events(client.post("/api/v1/mcp/register/completion/hitl/approve", json={"task_id": "test-mcp", "interrupt_id": "approval"}, headers=protocol_headers))
    assert approved[-1]["outcome"]["type"] == "success"
    assert client.post("/api/v1/mcp/register/completion/hitl/approve", json={"task_id": "test-mcp"}, headers=protocol_headers).status_code == 409

    client.post("/api/v1/user/register", json={"user_name": "other_user", "user_email": "other@example.test", "user_password": "local-test"})
    other_token = client.post("/api/v1/user/login", json={"user_name": "other_user", "user_password": "local-test"}).json()["data"]["access_token"]
    other_headers = {**protocol_headers, "Authorization": "Bearer " + other_token}
    # 即使旧配置放行 MCP 路径，聊天也必须校验真实身份并隔离读写。
    task_root = "/api/v1/mcp/register/task"
    client.cookies.clear()
    assert client.get(task_root + "/list").status_code == 401
    assert client.post(task_root + "/create").status_code == 401
    own_tasks = client.get(task_root + "/list", headers=protocol_headers).json()["data"]
    assert [task["id"] for task in own_tasks] == ["test-mcp"]
    assert client.get(task_root + "/list", headers=other_headers).json()["data"] == []
    other_task = client.post(task_root + "/create", headers=other_headers).json()["data"]
    assert other_task["user_id"] != own_tasks[0]["user_id"]
    for decision in ("approve", "reject"):
        assert client.post("/api/v1/mcp/register/completion/hitl/" + decision, json={"task_id": "test-mcp"}, headers=other_headers).status_code == 403
    assert client.post(task_root + "/delete", json={"task_id": "test-mcp"}, headers=other_headers).status_code == 403
    assert client.get(task_root + "/list", headers=protocol_headers).json()["data"] == own_tasks
    assert client.post(task_root + "/delete", json={"task_id": other_task["id"]}, headers=other_headers).status_code == 200
    assert client.get(task_root + "/list", headers=other_headers).json()["data"] == []
    assert client.post("/api/v1/completion", json={"conversation_id": conversation_id, "user_input": "forbidden"}, headers=other_headers).status_code == 403
    assert client.post("/api/v1/mcp/register/completion", json={"task_id": "test-mcp", "query": "forbidden"}, headers=other_headers).status_code == 403
    # 两个账号的默认资源拥有不同 ID，普通管理接口也不向管理员暴露他人资源。
    categories = [
        ("/api/v1/agent", "GET", "id"),
        ("/api/v1/tool/all", "POST", "tool_id"),
        ("/api/v1/agent_skill/all", "GET", "id"),
        ("/api/v1/mcp_server", "GET", "mcp_server_id"),
    ]
    other_server = client.get("/api/v1/mcp_server", headers=other_headers).json()["data"][0]["mcp_server_id"]
    configured = client.put("/api/v1/mcp_user_config/update", json={"server_id": other_server, "config": [{"key": "token", "value": "private-token"}]}, headers=other_headers)
    assert configured.json()["status_code"] == 200, configured.text
    config_id = client.get("/api/v1/mcp_user_config", params={"server_id": other_server}, headers=other_headers).json()["data"]["id"]
    forbidden_config = client.get("/api/v1/mcp_user_config/" + config_id, headers=protocol_headers)
    assert forbidden_config.json()["status_code"] == 500 and "private-token" not in forbidden_config.text
    assert client.request("DELETE", "/api/v1/mcp_user_config/delete", json={"config_id": config_id}, headers=protocol_headers).json()["status_code"] == 500
    private = []
    other_user_id = client.get("/api/v1/agent", headers=other_headers).json()["data"][0]["user_id"]
    for url, method, key in categories:
        first = client.request(method, url, headers=protocol_headers).json()["data"]
        second = client.request(method, url, headers=other_headers).json()["data"]
        if url == "/api/v1/mcp_server":
            import json
            from pathlib import Path
            templates = json.loads(Path("agentchat/config/mcp_server.json").read_text(encoding="utf-8"))
            for server in first + second:
                template = next(config for config in templates if config["url"] == server["url"])
                assert server["tools"] == template["tools"]
                assert server["params"] == template["params"]
                assert server["tools"]
        assert first and second and len(first) == len(second)
        assert {row[key] for row in first}.isdisjoint({row[key] for row in second})
        assert all(row["user_id"] == login.json()["data"]["user_id"] for row in first)
        assert all(row["user_id"] == other_user_id for row in second)
        private.append((url, method, key, first, second))
    attacks = [
        ("PUT", "/api/v1/agent", {"agent_id": private[0][4][0]["id"], "name": "forbidden"}),
        ("POST", "/api/v1/tool/update", {"tool_id": private[1][4][0]["tool_id"], "description": "forbidden"}),
        ("POST", "/api/v1/agent_skill/update", {"agent_skill_id": private[2][4][0]["id"], "name": "forbidden", "description": "forbidden"}),
        ("DELETE", "/api/v1/mcp_server", {"server_id": private[3][4][0]["mcp_server_id"]}),
        ("PUT", "/api/v1/agent", {"agent_id": agent_id, "tool_ids": [private[1][4][0]["tool_id"]]}),
    ]
    for method, url, body in attacks:
        result = client.request(method, url, json=body, headers=protocol_headers)
        assert result.json().get("status_code") == 500, result.text
    own_skill = private[2][3][0]
    edited = client.post("/api/v1/agent_skill/update", json={"agent_skill_id": own_skill["id"], "name": "my skill", "description": own_skill["description"]}, headers=protocol_headers)
    assert edited.json()["status_code"] == 200, edited.text
    for url, method, key, first, second in private:
        current = client.request(method, url, headers=other_headers).json()["data"]
        assert current == second
    deletions = [
        ("DELETE", "/api/v1/agent", {"agent_id": private[0][3][0]["id"]}),
        ("POST", "/api/v1/tool/delete", {"tool_id": private[1][3][0]["tool_id"]}),
        ("POST", "/api/v1/agent_skill/delete", {"agent_skill_id": own_skill["id"]}),
        ("DELETE", "/api/v1/mcp_server", {"server_id": private[3][3][0]["mcp_server_id"]}),
    ]
    for method, url, body in deletions:
        result = client.request(method, url, json=body, headers=protocol_headers)
        assert result.json()["status_code"] == 200, result.text
    for url, method, key, first, second in private:
        assert len(client.request(method, url, headers=protocol_headers).json()["data"]) == len(first) - 1
        assert client.request(method, url, headers=other_headers).json()["data"] == second
    print("SIMPLE_APP_OK")
'''
    env = {
        **os.environ,
        "AGENTCHAT_CONFIG": str(path),
        "AGENTCHAT_LOG_DIR": str(tmp_path / "logs"),
        "PYTHONUTF8": "1",
    }
    result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parents[1],
                            env=env, capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-6000:]
    assert "SIMPLE_APP_OK" in result.stdout
    assert (tmp_path / "app.db").is_file()
    # 使用新进程证明文件在重启后仍可读取。
    restart = subprocess.run([sys.executable, "-c", '''
import asyncio
from agentchat.settings import init_app_settings
asyncio.run(init_app_settings())
from agentchat.services.storage import storage_client
files = list(storage_client.root.rglob("*.txt"))
assert any(p.read_bytes() == b"local upload" for p in files)
print("LOCAL_FILES_RETAINED")
'''], cwd=Path(__file__).parents[1], env=env, capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert restart.returncode == 0, restart.stderr
