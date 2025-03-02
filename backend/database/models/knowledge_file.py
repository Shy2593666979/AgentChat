from datetime import datetime

import pytz
from sqlmodel import Session, SQLModel, Field
from uuid import uuid4

class KnowledgeFileTable(SQLModel, table=True):
    id: str = Field(default=uuid4().hex, description='知识库文件id', primary_key=True)
    file_name: str = Field(index=True)
    knowledge_id: str = Field(index=True)
    user_id: str = Field(index=True)
    oss_url: str = Field(default=None)
    update_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))