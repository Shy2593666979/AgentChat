from types import SimpleNamespace

import yaml
from loguru import logger
from pydantic.v1 import BaseSettings

from agentchat.schema.common import MultiModels, ModelConfig


class Settings(BaseSettings):
    llm: dict = {}
    aliyun_oss: dict = {}
    rag: dict = {}
    logo: dict = {}
    redis: dict = {}
    mysql: dict = {}
    rerank: dict = {}
    server: dict = {}
    split: dict = {}
    vector_db: dict = {}
    embedding: dict = {}
    langfuse: dict = {}
    elasticsearch: dict = {}
    tool_delivery: dict = {}
    tool_google: dict = {}
    tool_weather: dict = {}
    tool_tavily: dict = {}
    whitelist_paths: list = []
    mars: dict = {}

    multi_models: MultiModels = MultiModels()

    use_oss: bool = False
    use_captcha: bool = False

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

            for key, value in data.items():
                setattr(app_settings, key, value)
    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")
