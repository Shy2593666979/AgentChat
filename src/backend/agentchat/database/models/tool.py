from enum import Enum
from uuid import uuid4
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime, text, JSON

from agentchat.database.models.base import SQLModelSerializable


class ToolAuthType(str, Enum):
    bearer: str = "Bearer"
    basic: str = "Basic"


class ToolTable(SQLModelSerializable, table=True):
    __tablename__ = "tool"

    tool_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: Optional[str] = Field(description='工具的英文名称，大模型调用')
    display_name: str = Field(description='工具的中文名称，显示给用户')
    user_id: str = Field(description='该工具对应的创建用户')
    logo_url: str = Field(description='工具对应的Logo地址')
    description: str = Field(sa_column=Column(Text), description='大模型将根据此描述识别并调用该工具')
    openapi_schema: Optional[dict] = Field(sa_column=Column(JSON), description="用户自定义添加工具的格式")
    is_user_defined: bool = Field(default=False, description="代表是否是自定义的工具")
    auth_config: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON), description="用户的鉴权信息")
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        ),
        description="修改时间"
    )
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )