from datetime import datetime
from typing import Optional, List

from sqlmodel import Field
from uuid import uuid4
from sqlalchemy import Column, Text, JSON, DateTime, text, ForeignKey, CHAR, func

from agentchat.database.models.base import SQLModelSerializable

class WorkBenchSessionBase(SQLModelSerializable):
    title: str = Field(..., description="工作台会话的标题")
    user_id: str = Field(..., description="工作台会话对应的User ID")
    contexts: List[dict] = Field(None, sa_column=Column(JSON), description="JSON, 含 tasks、questions、answers、guide_prompts 四个字段的结构化对话上下文")

    # tasks: List[str] = Field(None, description="工作台会话的任务")
    # questions: List[str] = Field(None, description="用户的问题列表")
    # answers: List[str] = Field(None, description="AI回复列表，对用户问题一一对应")
    # guide_prompts: List[str] = Field(None, description="AI生成")

class WorkBenchSession(WorkBenchSessionBase, table=True):
    __tablename__ = "workbench_session"

    session_id = Field(default_factory=lambda: uuid4().hex, primary_key=True, description="工作台的会话ID")

    update_time: Optional[datetime] = Field(sa_column=Column(
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