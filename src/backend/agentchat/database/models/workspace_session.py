from datetime import datetime
from typing import Optional, List

from sqlmodel import Field
from uuid import uuid4
from pydantic import BaseModel
from sqlalchemy import Column, Text, JSON, DateTime, text, ForeignKey, CHAR, func

from agentchat.database.models.base import SQLModelSerializable

class WorkSpaceSessionBase(SQLModelSerializable):
    title: str = Field(..., description="工作台会话的标题")
    agent: str = Field(..., description="工作台中选用的智能体")
    user_id: str = Field(..., description="工作台会话对应的User ID")
    contexts: List[dict] = Field([], sa_column=Column(JSON), description="JSON, 含 tasks、questions、answers、guide_prompts 四个字段的结构化对话上下文")

    # tasks: List[str] = Field(None, description="工作台会话的任务")
    # questions: List[str] = Field(None, description="用户的问题列表")
    # answers: List[str] = Field(None, description="AI回复列表，对用户问题一一对应")
    # guide_prompts: List[str] = Field(None, description="AI生成")

class WorkSpaceSession(WorkSpaceSessionBase, table=True):
    __tablename__ = "workspace_session"

    session_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, description="工作台的会话ID")

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

class WorkSpaceSessionCreate(BaseModel):
    title: str
    agent: str
    user_id: str
    session_id: str = None  # 允许传入session_id，如果为None则自动生成
    contexts: list[dict] = []

class WorkSpaceSessionContext(BaseModel):
    query: str
    guide_prompt: str = ""
    task: list[dict] = []
    task_graph: list[dict] = []
    answer: str
