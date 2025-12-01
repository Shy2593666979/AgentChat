from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import JSON, Column, DateTime, text

from agentchat.database.models.base import SQLModelSerializable


# 每个MCPAgent
class MCPAgentTable(SQLModelSerializable, table=True):
    __tablename__ = "mcp_agent"

    mcp_agent_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    mcp_server_id: str = Field(default=[], sa_column=Column(JSON), description='MCPAgent绑定的工具列表')
    name: str = Field(default="", description="MCP Agent的名称")
    description: str = Field(default='')
    logo_url: str = Field(default='img/mcp_openai/mcp_agent.png')
    user_id: Optional[str] = Field(index=True)

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
