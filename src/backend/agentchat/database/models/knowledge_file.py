from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import DateTime, text, Column
from sqlmodel import Session, SQLModel, Field
from uuid import uuid4

from agentchat.database.models.base import SQLModelSerializable

class Status:
    fail = "fail"
    process = "process"
    success = "success"

class KnowledgeFileTable(SQLModelSerializable, table=True):
    __tablename__ = "knowledge_file"

    id: str = Field(default=uuid4().hex, description='知识库文件id', primary_key=True)
    file_name: str = Field(index=True, description="知识库的名称")
    knowledge_id: str = Field(index=True, description="知识库的ID")
    status: str = Field(default=Status.success, description="文件解析的状态 ")
    user_id: str = Field(index=True, description="用户ID")
    oss_url: str = Field(default="", description="知识库文件保存到oss的路径")
    file_size: int = Field(default=0,description="文件大小（单位：字节），如317440表示310KB")
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