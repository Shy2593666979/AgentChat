from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column
import pytz

from agentchat.database.models.base import SQLModelSerializable


class AgentTable(SQLModelSerializable, table=True):
    __tablename__ = "agent"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(default="")
    description: str = Field(default="")
    logo_url: str = Field(default="https://agentchat.oss-cn-beijing.aliyuncs.com/icons/bot.png")
    user_id: Optional[str] = Field(index=True)
    is_custom: bool = Field(default=True)
    system_prompt: str = Field(default="", description="Agent设定的系统提示词")
    llm_id: str = Field(default="", description="Agent绑定的LLM模型")
    use_embedding: bool = Field(default=True, description="是否开启RAG检索历史记录")
    mcp_ids: List[str] = Field(default=[], sa_column=Column(JSON), description="Agent绑定的MCP Server")
    tool_ids: List[str] = Field(default=[], sa_column=Column(JSON), description="Agent绑定的工具列表")
    knowledge_ids: List[str] = Field(default=[], sa_column=Column(JSON), description="Agent 绑定的知识库")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone("Asia/Shanghai")))
