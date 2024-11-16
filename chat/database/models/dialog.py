from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4
import pytz

# 每个对话
class DialogTable(SQLModel, table=True):
    dialogId: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    agent: str
    createTime: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
