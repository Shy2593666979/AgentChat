from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel



class UserRoleBase(SQLModel):
    user_id: str = Field(index=True)
    role_id: str = Field(index=True)
    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    update_time: Optional[datetime] = Field(
        sa_column=Column(DateTime,
                         nullable=False,
                         index=True,
                         server_default=text('CURRENT_TIMESTAMP'),
                         onupdate=text('CURRENT_TIMESTAMP')))


class UserRole(UserRoleBase, table=True):
    __tablename__ = "user_role"
    id: Optional[str] = Field(default=None, primary_key=True)


class UserRoleRead(UserRoleBase):
    id: Optional[str]


class UserRoleCreate(BaseModel):
    user_id: str
    role_id: list[str]

