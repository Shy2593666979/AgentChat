import os
import yaml
from loguru import logger
from types import SimpleNamespace
from pydantic.v1 import BaseSettings, Field

from agentchat.schema.common import MultiModels, ModelConfig, Tools, Rag

class Settings(BaseSettings):
    aliyun_oss: dict = {}
    redis: dict = {}
    mysql: dict = {}
    server: dict = {}
    langfuse: dict = {}
    whitelist_paths: list = []
    wechat_config: dict = {}
    multi_models: MultiModels = MultiModels()
    default_config: dict = {}

    tools: Tools = Tools()

    rag: Rag = Rag()


app_settings = Settings()

async def initialize_app_settings(file_path: str = None):
    global app_settings

    file_path = file_path or "agentchat/config.yaml"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.error("YAML 文件解析为空")
                return

            # 特殊处理multi_models配置
            if 'multi_models' in data:
                # 将字典转换为可以用点号访问的对象
                models_config = SimpleNamespace()
                for model_name, model_config in data['multi_models'].items():
                    setattr(models_config, model_name, ModelConfig(**model_config))
                data['multi_models'] = models_config

            if 'tools' in data:
                tools_config = SimpleNamespace()
                for tool_name, tool_config in data['tools'].items():
                    setattr(tools_config, tool_name, tool_config)
                data['tools'] = tools_config

            if 'rag' in data:
                rag_configs = SimpleNamespace()
                for rag_name, rag_config in data['rag'].items():
                    setattr(rag_configs, rag_name, rag_config)
                data['rag'] = rag_configs


            for key, value in data.items():
                setattr(app_settings, key, value)


            # ✅ 新增核心逻辑：用环境变量覆盖配置（Docker环境生效）
            # 覆盖 MySQL 配置
            if os.getenv("MYSQL_ENDPOINT"):
                app_settings.mysql["endpoint"] = os.getenv("MYSQL_ENDPOINT")
            if os.getenv("MYSQL_ASYNC_ENDPOINT"):
                app_settings.mysql["async_endpoint"] = os.getenv("MYSQL_ASYNC_ENDPOINT")
            
            # 覆盖 Redis 配置
            if os.getenv("REDIS_ENDPOINT"):
                app_settings.redis["endpoint"] = os.getenv("REDIS_ENDPOINT")
            
            # 覆盖 Server 监听地址
            if os.getenv("SERVER_HOST"):
                app_settings.server["host"] = os.getenv("SERVER_HOST")


    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")
