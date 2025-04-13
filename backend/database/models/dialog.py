from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4
import pytz
from typing import Literal


# 每个对话
class DialogTable(SQLModel, table=True):
    dialog_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(description='对话绑定的Agent的名称')
    agent_id: str = Field(description='对话Dialog绑定Agent的ID')
    agent_type: Literal["Agent", "MCPAgent"] = Field(default="Agent", description="对话Dialog绑定Agent, MCPAgent or Agent")
    user_id: str = Field(description='对话Dialog的用户ID')
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
