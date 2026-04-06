from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, Text, Relationship, DateTime, select, delete

from agentchat.utils.common import generate_uuid, get_now_time

if TYPE_CHECKING:
    from agentchat.database.models.register_mcp_tool import RegisterMcpTool

class RegisterMcpServer(SQLModel, table=True):
    __tablename__ = "register_mcp_server"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    name: str = Field(max_length=255)
    transport: str = Field(default="sse")
    remote_url: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_time: datetime = Field(
        default_factory=get_now_time,
        sa_column=Column(DateTime, nullable=False, default=get_now_time)
    )
    updated_time: datetime = Field(
        default_factory=get_now_time,
        sa_column=Column(DateTime, nullable=False, default=get_now_time, onupdate=get_now_time)
    )

    mcp_tools: List["RegisterMcpTool"] = Relationship(back_populates="mcp_server")



