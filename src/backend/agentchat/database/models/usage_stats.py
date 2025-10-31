from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from sqlmodel import Field
from sqlalchemy import Column, DateTime, text

from agentchat.database.models.base import SQLModelSerializable

class UsageStatsBase(SQLModelSerializable):
    agent: Optional[str] = Field(description="使用统计的智能体")
    model: Optional[str] = Field(description="使用统计的模型")

    user_id: str = Field(..., description="发起请求的用户唯一标识（UUID 或系统用户 ID）")

    input_token: int = Field(ge=0, description="输入（prompt）所消耗的 token 数量")
    output_token: int = Field(ge=0, description="模型生成（completion）所消耗的 token 数量")
    total_token: int = Field(ge=0, description="总 token 数量，通常为 input_token + output_token")

    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )

class UsageStats(UsageStatsBase, table=True):
    id: str = Field(..., description="智能体、模型的使用统计的ID")
