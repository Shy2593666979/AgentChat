from typing import Optional
from pydantic import BaseModel, Field

class KnowledgeCreateRequest(BaseModel):
    knowledge_name: str = Field(description="知识库名称", min_length=2, max_length=10)
    knowledge_desc: str = Field(description="知识库的描述", min_length=2, max_length=200)

class KnowledgeUpdateRequest(BaseModel):
    knowledge_id: str = Field(description="知识库ID")
    knowledge_name: str = Field(description="知识库名称", min_length=2, max_length=10)
    knowledge_desc: str = Field(description="知识库的描述", min_length=2, max_length=200)