from datetime import datetime
from typing import List, Optional

from pydantic import validator, BaseModel
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field

# 系统用户
SystemUser = 0
# 管理员
AdminUser = 1


class UserBase(BaseModel):
    user_name: str = Field(index=True, unique=True)
    email: Optional[str] = Field(index=True)
    dept_id: Optional[str] = Field(index=True)
    remark: Optional[str] = Field(index=False)
    delete: int = Field(index=False, default=0)
    create_time: Optional[datetime] = Field(sa_column=Column(
        DateTime, nullable=False, index=True, server_default=text('CURRENT_TIMESTAMP')))
    update_time: Optional[datetime] = Field(
        sa_column=Column(DateTime,
                         nullable=False,
                         server_default=text('CURRENT_TIMESTAMP'),
                         onupdate=text('CURRENT_TIMESTAMP')))

    @validator('user_name')
    def validate_str(v):
        # dict_keys(['description', 'name', 'id', 'data'])
        if not v:
            raise ValueError('user_name 不能为空')
        return v


class User(UserBase, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    password: str = Field(index=False)
    password_update_time: Optional[datetime] = Field(sa_column=Column(DateTime,
                                                                      nullable=False,
                                                                      server_default=text('CURRENT_TIMESTAMP')),
                                                     description="密码最近的修改时间")

class UserRead(UserBase):
    user_id: Optional[int]
    role: Optional[str]
    access_token: Optional[str]
    admin_groups: Optional[List[int]]  # 所管理的用户组ID列表


class UserQuery(UserBase):
    user_id: Optional[int]
    user_name: Optional[str]


class UserLogin(UserBase):
    password: str
    user_name: str


class UserCreate(UserBase):
    password: Optional[str] = Field(default="")


class UserUpdate(BaseModel):
    user_id: int
    delete: Optional[int] = 0
