from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text
from datetime import datetime
from uuid import uuid4
import pytz

class ToolTable(SQLModel, table=True):
    tool_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    zh_name: str = Field(description='工具的中文名称，显示给用户')
    en_name: str = Field(description='工具的英文名称，大模型调用')
    user_id: str = Field(description='该工具对应的创建用户')
    description: str = Field(sa_column=Column(Text), description='大模型将根据此描述识别并调用该工具')
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))