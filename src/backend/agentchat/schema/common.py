from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class ModelConfig(BaseModel):
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""

class MultiModels(BaseModel):
    class Config:
        # 允许从dict额外属性创建模型
        extra = "allow"

    reasoning_model: ModelConfig = Field(default_factory=ModelConfig)
    conversation_model: ModelConfig = Field(default_factory=ModelConfig)
    tool_call_model: ModelConfig = Field(default_factory=ModelConfig)
    qwen3_coder: ModelConfig = Field(default_factory=ModelConfig)
    qwen_vl: ModelConfig = Field(default_factory=ModelConfig)
    text2image: ModelConfig = Field(default_factory=ModelConfig)
    embedding: ModelConfig = Field(default_factory=ModelConfig)
    rerank: ModelConfig = Field(default_factory=ModelConfig)

class Tools(BaseModel):
    class Config:
        extra = "allow"

    weather: dict = Field(default_factory=dict)
    tavily: dict = Field(default_factory=dict)
    google: dict = Field(default_factory=dict)
    delivery: dict = Field(default_factory=dict)
    bocha: dict = Field(default_factory=dict)


class Rag(BaseModel):
    class Config:
        extra = "allow"

    enable_elasticsearch: bool = Field(default=False)
    enable_summary: bool = Field(default=False)
    retrival: dict = Field(default_factory=dict)
    split: dict = Field(default_factory=dict)
    elasticsearch: dict = Field(default_factory=dict)
    vector_db: dict = Field(default_factory=dict)



class OSSConfig(BaseModel):
    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    base_url: str


class MinioConfig(BaseModel):
    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    base_url: str

class StorageConfig(BaseModel):
    mode: Literal["oss", "minio"]
    oss: Optional[OSSConfig] = None
    minio: Optional[MinioConfig] = None

    @model_validator(mode="after")
    def validate_storage(self):
        if self.mode == "oss" and not self.oss:
            raise ValueError("mode=oss 时必须提供 aliyun_oss")
        if self.mode == "minio" and not self.minio:
            raise ValueError("mode=minio 时必须提供 minio")
        return self

    @property
    def active(self):
        return self.oss if self.mode == "oss" else self.minio