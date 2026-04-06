from pydantic import BaseModel, Field

class CreateUserReq(BaseModel):
    user_name: str = Field(max_length=20, description='创建用户时的名称')
    password: str = Field(description='创建用户时的密码')