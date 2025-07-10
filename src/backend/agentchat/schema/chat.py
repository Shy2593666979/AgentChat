from pydantic import BaseModel, Field


class ConversationReq(BaseModel):
    user_input: str = Field(description="用户的问题")
    dialog_id: str = Field(description="对话的ID值")
    file_url: str = Field(None, description="对话中上传的文件的oss链接")