from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, Text, JSON, Relationship, DateTime
from datetime import datetime

from agentchat.utils.common import generate_uuid, get_now_time

if TYPE_CHECKING:
    from agentchat.database.models.register_mcp import RegisterMcpServer

class RegisterMcpTool(SQLModel, table=True):
    __tablename__ = "register_mcp_tool"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    register_mcp_id: str = Field(index=True, max_length=64, foreign_key="register_mcp_server.id")
    name: str = Field(max_length=1024)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    parameters: Optional[str] = Field(default=None, sa_column=Column(Text))
    api_info: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_time: datetime = Field(
        default_factory=get_now_time,
        sa_column=Column(DateTime, nullable=False, default=get_now_time)
    )
    updated_time: datetime = Field(
        default_factory=get_now_time,
        sa_column=Column(DateTime, nullable=False, default=get_now_time, onupdate=get_now_time)
    )

    mcp_server: Optional["RegisterMcpServer"] = Relationship(back_populates="mcp_tools")


