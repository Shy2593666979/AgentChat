from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, DateTime, text, UniqueConstraint
from sqlmodel import Field, SQLModel

# 默认普通用户角色的ID
DefaultRole = '2'
# 超级管理员角色ID
AdminRole = '1'
# 系统管理员角色
SystemRole = '0'

class RoleBase(SQLModel):
    role_name: str = Field(index=False, description='前端展示名称')
    remark: Optional[str] = Field(index=False)
    create_time: Optional[datetime] = Field(sa_column=Column(
        DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP')))
    update_time: Optional[datetime] = Field(
        sa_column=Column(DateTime,
                         nullable=False,
                         server_default=text('CURRENT_TIMESTAMP'),
                         onupdate=text('CURRENT_TIMESTAMP')))


class Role(RoleBase, table=True):
    __table_args__ = (UniqueConstraint('role_name', name='group_role_name_uniq'),)
    id: Optional[int] = Field(default=None, primary_key=True)


class RoleRead(RoleBase):
    id: Optional[int]


class RoleUpdate(RoleBase):
    role_name: Optional[str]
    remark: Optional[str]


class RoleCreate(RoleBase):
    pass
