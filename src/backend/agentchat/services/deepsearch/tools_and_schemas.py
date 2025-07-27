from typing import List
from pydantic import BaseModel, Field


class SearchQueryList(BaseModel):
    query: List[str] = Field(
        description="用于网络研究的搜索查询列表。"
    )
    rationale: str = Field(
        description="简要解释这些查询与研究主题的相关性。"
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="提供的摘要是否足以回答用户的问题。"
    )
    knowledge_gap: str = Field(
        description="对缺失信息或需要澄清的内容的描述。"
    )
    follow_up_queries: List[str] = Field(
        description="解决知识缺口的后续查询列表。"
    )