import orjson
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import validator, BaseModel
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel

from agentchat.database.models.base import SQLModelSerializable

# 系统用户
SystemUser = '0'
# 管理员
AdminUser = '1'


class UserTable(SQLModelSerializable, table=True):
    __tablename__ = "user"

    user_id: str = Field(primary_key=True)
    user_name: str = Field(index=True, unique=True)
    user_email: str = Field(default=None)
    user_avatar: str = Field(description="用户头像")
    user_description: str = Field(default="该用户很懒，没有留下一片云彩")
    user_password: str = Field(description='经过加密后的用户密码')
    delete: bool = Field(default=False, description='该用户是否删除')
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


# class User(UserBase, table=True):
#     user_id: Optional[str] = Field(default=None, primary_key=True)
#     password: str = Field(index=False)
#     password_update_time: Optional[datetime] = Field(sa_column=Column(DateTime,
#                                                                       nullable=False,
#                                                                       server_default=text('CURRENT_TIMESTAMP')),
#                                                      description="密码最近的修改时间")
#
# class UserRead(UserBase):
#     user_id: Optional[str]
#     role: Optional[str]
#     access_token: Optional[str]
#     admin_groups: Optional[List[int]]  # 所管理的用户组ID列表
#
#
# class UserQuery(UserBase):
#     user_id: Optional[str]
#     user_name: Optional[str]
#
#
# class UserLogin(UserBase):
#     password: str
#     user_name: str
#
#
# class UserCreate(UserBase):
#     password: Optional[str] = Field(default="")
#
#
# class UserUpdate(BaseModel):
#     user_id: str
#     delete: Optional[int] = 0

# def orjson_dumps(v, *, default=None, sort_keys=False, indent_2=True):
#     option = orjson.OPT_SORT_KEYS if sort_keys else None
#     if indent_2:
#         # orjson.dumps returns bytes, to match standard json.dumps we need to decode
#         # option
#         # To modify how data is serialized, specify option. Each option is an integer constant in orjson.
#         # To specify multiple options, mask them together, e.g., option=orjson.OPT_STRICT_INTEGER | orjson.OPT_NAIVE_UTC
#         if option is None:
#             option = orjson.OPT_INDENT_2
#         else:
#             option |= orjson.OPT_INDENT_2
#     if default is None:
#         return orjson.dumps(v, option=option).decode()
#     return orjson.dumps(v, default=default, option=option).decode()
#
#
# class SQLModelSerializable(SQLModel):
#
#     class Config:
#         orm_mode = True
#         json_loads = orjson.loads
#         json_dumps = orjson_dumps
#
#     def to_dict(self):
#         result = self.model_dump()
#         for column in result:
#             value = getattr(self, column)
#             if isinstance(value, datetime):
#                 # 将datetime对象转换为字符串
#                 value = value.isoformat()
#             elif isinstance(value, UUID):
#                 # 将UUID对象转换为字符串
#                 value = value.hex
#             result[column] = value
#         return result
