import os
from copy import deepcopy
from pathlib import Path

import yaml
from loguru import logger
from pydantic.v1 import BaseSettings

from agentchat.schemas.common import (
    MultiModels,
    Rag,
    ServerConfig,
    StorageConfig,
    Tools,
)


class Settings(BaseSettings):
    log_level: str = "INFO"
    redis: dict = {}
    mysql: dict = {}
    database: dict = {}
    langfuse: dict = {}
    whitelist_paths: list = []
    wechat_config: dict = {}
    default_config: dict = {}
    simple_mode: bool = False
    server: ServerConfig = ServerConfig()
    rag: Rag | None = None
    tools: Tools | None = None
    storage: StorageConfig | None = None
    multi_models: MultiModels | None = None


def default_config() -> dict:
    """默认值独立于完整配置，避免简易模式继承外部服务凭据。"""
    return {
        "server": {},
        "database": {
            "url": "sqlite:///data/agentchat.db",
        },
        "redis": {
            "endpoint": None,
        },
        "storage": {
            "mode": "local",
            "local": {
                "path": "data/uploads",
                "base_url": "http://127.0.0.1:7860/uploads/",
            },
        },
        "multi_models": {},
        "tools": {
            name: {
                "api_key": "",
            }
            for name in (
                "weather",
                "tavily",
                "google",
                "delivery",
                "bocha",
                "serply",
                "youcom",
            )
        },
        "rag": {
            "enable_summary": False,
            "enable_elasticsearch": False,
            "retrival": {
                "top_k": 5,
                "min_score": 0.2,
            },
            "split": {
                "chunk_size": 500,
                "overlap_size": 100,
            },
            "vector_db": {
                "mode": "chroma",
            },
            "elasticsearch": {},
        },
        "default_config": {
            "memory_collection_name": "memory",
            "mcp_logo_url": "",
            "tool_logo_url": "",
            "agent_logo_url": "",
            "mars_daily_url": "https://news.aibase.com/zh/news",
        },
        "whitelist_paths": ["/mcp/*", "/uploads/*"],
        "mysql": {},
        "langfuse": {},
        "wechat_config": {},
        "simple_mode": False,
    }


def merge_config(defaults: dict, overrides: dict) -> dict:
    """逐层覆盖配置，保留未填写字段的默认值。"""
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_settings(file_path: str | Path) -> Settings:
    data = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("配置文件必须包含 YAML 配置项")
    defaults = default_config()
    simple = data.get("simple_mode") is True or "model" in data
    if simple:
        # 保留完整配置的多模型结构，同时兼容之前的单模型简写。
        model = data.pop("model") if "model" in data else data.get("multi_models", {}).get("chat_model")
        if not isinstance(model, dict) or not isinstance(model.get("api_key"), str) or not model["api_key"].strip():
            raise ValueError("简易配置必须填写 multi_models.chat_model.api_key（或 model.api_key）")
        conversation = {
            "api_key": model["api_key"].strip(),
            "base_url": model.get(
                "base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
            "model_name": model.get("model_name", "qwen-plus"),
        }
        defaults["multi_models"] = {
            name: deepcopy(conversation)
            for name in (
                "chat_model",
                "tool_call_model",
                "reasoning_model",
                "qwen3_coder",
            )
        }
        # 同一个通义 Key 可用于知识库向量化；其他服务商可通过高级字段覆盖。
        defaults["multi_models"]["embedding"] = {
            **conversation,
            "model_name": "text-embedding-v4",
        }
        defaults["multi_models"]["qwen_vl"] = {
            **conversation,
            "model_name": "qwen-vl-plus",
        }
        defaults["multi_models"]["rerank"] = {
            **conversation,
            "model_name": "gte-rerank-v2",
            "base_url": "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
        }
    merged = merge_config(defaults, data)
    merged["simple_mode"] = simple
    if "mysql" in data and "database" not in data:
        # 兼容旧版 MySQL 配置，不能让 SQLite 默认值覆盖显式选择。
        merged["database"] = {}
    if merged["storage"]["mode"] == "local" and not data.get("storage", {}).get("local", {}).get("base_url"):
        server = ServerConfig(**merged["server"])
        host = "127.0.0.1" if server.host == "0.0.0.0" else server.host
        merged["storage"]["local"]["base_url"] = f"http://{host}:{server.port}/uploads/"
    for name, schema in (("multi_models", MultiModels), ("tools", Tools), ("rag", Rag),
                         ("storage", StorageConfig), ("server", ServerConfig)):
        merged[name] = schema(**merged[name])
    return Settings(**merged)


app_settings = Settings()


async def init_app_settings(file_path: str | Path = None):
    if file_path is None:
        selected = os.getenv("AGENTCHAT_CONFIG")
        local_config = Path(__file__).with_name("config.local.yaml")
        file_path = selected or (local_config if local_config.is_file() else Path(__file__).with_name("config.yaml"))
    # 先完整校验再更新共享对象，加载失败直接阻止启动，避免混用旧配置。
    settings = load_settings(file_path)
    for key in settings.__fields__:
        setattr(app_settings, key, getattr(settings, key))
    logger.info("已加载配置文件：{}", Path(file_path).name)
