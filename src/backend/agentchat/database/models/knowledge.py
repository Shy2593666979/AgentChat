import pytz
from sqlmodel import Field, SQLModel
from typing import Literal, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, Column

from agentchat.database.models.base import SQLModelSerializable


class KnowledgeTable(SQLModelSerializable, table=True):
    __tablename__ = "knowledge"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(index=True)
    user_id: Optional[str] = Field(index=True)
    update_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
