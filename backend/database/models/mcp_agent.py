from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column
import pytz

# 每个MCPAgent
class MCPAgentTable(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(default='')
    description: str = Field(default='')
    logo: str = Field(default='img/mcp/mcp_agent.png')
    user_id: Optional[str] = Field(index=True)
    is_custom: bool = Field(default=True)
    llm_id: str = Field(default=None, description='MCPAgent绑定的LLM模型')
    use_embedding: bool = Field(default=True, description='是否开启RAG检索历史记录')
    mcp_servers_id: List[str] = Field(default=[], sa_column=Column(JSON), description='MCPAgent绑定的工具列表')
    knowledges_id: List[str] = Field(default=[], sa_column=Column(JSON), description="MCPAgent 绑定的知识库")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
