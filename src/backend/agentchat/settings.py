import yaml
from loguru import logger
from pydantic.v1 import BaseSettings

from agentchat.schema.common import MultiModels


class Settings(BaseSettings):
    llm: dict = {}
    aliyun_oss: dict = {}
    rag: dict = {}
    logo: dict = {}
    redis: dict = {}
    mysql: dict = {}
    milvus: dict = {}
    rerank: dict = {}
    server: dict = {}
    split: dict = {}
    embedding: dict = {}
    langfuse: dict = {}
    elasticsearch: dict = {}
    tool_delivery: dict = {}
    tool_google: dict = {}
    tool_weather: dict = {}
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
            else:
                for key, value in data.items():
                    setattr(app_settings, key, value)
    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")