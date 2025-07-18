from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column, text, DateTime
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

    # 修改时间，默认为当前时间戳，自动更新
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        ),
        description="修改时间"
    )

    # 创建时间，默认为当前时间戳
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )
