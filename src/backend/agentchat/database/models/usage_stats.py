from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field

from agentchat.database.models.base import SQLModelSerializable


class UsageStatsBase(SQLModelSerializable):
    agent: Optional[str] = Field(description="使用统计的智能体")
    model: Optional[str] = Field(description="使用统计的模型")

    user_id: str = Field(..., description="发起请求的用户唯一标识（UUID 或系统用户 ID）")
    conversation_id: Optional[str] = Field(default=None, max_length=64, index=True, description="模型调用所属会话 ID，非会话调用或旧记录为空")

    input_tokens: int = Field(0, description="输入（prompt）所消耗的 token 数量")
    output_tokens: int = Field(0, description="模型生成（completion）所消耗的 token 数量")

    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )

class UsageStats(UsageStatsBase, table=True):
    __tablename__ = "usage_stats"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True, description="智能体、模型的使用统计的ID")
