import uuid
from datetime import datetime
from typing import List, Dict, Optional
from sqlmodel import Field, Column, JSON, DateTime, text
from agentchat.database.models.base import SQLModelSerializable


class AgentSkill(SQLModelSerializable, table=True):
    __tablename__ = "agent_skill"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, description="Agent Skill的ID")
    name: str = Field(..., description="Agent Skill的名称")
    description: str = Field(..., description="Agent Skill的描述信息")
    user_id: str = Field(..., description="Agent Skill的拥有者")
    as_tool_name: Optional[str] = Field(description="Agent Skill当作Tool的名称")
    folder: Optional[Dict] = Field(
        sa_column=Column(JSON),
        description="存放的是Agent Skill的目录以及文件信息"
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