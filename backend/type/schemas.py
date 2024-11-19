from typing import Any, TypeVar, Generic
from pydantic import BaseModel
from sqlmodel import Field

# 创建泛型变量
DataT = TypeVar('DataT')


class CreateUserReq(BaseModel):
    user_name: str = Field(max_length=20, description='创建用户时的名称')
    password: str = Field(description='创建用户时的密码')

class UnifiedResponseModel(Generic[DataT], BaseModel):
    """统一响应模型"""
    status_code: int
    status_message: str
    data: DataT = None

def resp_200(data: Any=None, code: int=200, message: str="SUCCESS"):
    return {
        "code": code,
        "message": message,
        "data": data
    }

def resp_500(data: Any=None, code: int=500, message: str="REQUEST ERROR"):
    return {
        "code": code,
        "message": message,
        "data": data
    }