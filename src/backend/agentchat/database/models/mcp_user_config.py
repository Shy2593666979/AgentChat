from typing import Optional, List
from sqlalchemy import Column, VARCHAR, JSON, text, DateTime
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4, UUID
from agentchat.database.models.base import SQLModelSerializable
import pytz


class MCPUserConfigTable(SQLModelSerializable, table=True):
    """
    MCP用户配置表，用于存储用户与MCP Server的绑定配置信息。
    """
    __tablename__ = "mcp_user_config"

    # 主键ID，使用UUID生成唯一标识
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, description="主键ID")

    # 绑定的MCP Server ID
    mcp_server_id: str = Field(description="绑定的MCP Server ID")

    # 绑定到该MCP Server的用户ID
    user_id: str = Field(description="绑定到该MCP Server的用户ID")

    # 针对一些需要鉴权的MCP Server的配置信息
    config: List[dict] = Field(
        sa_column=Column(JSON),
        description="针对一些需要鉴权的MCP Server的配置信息"
    )

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