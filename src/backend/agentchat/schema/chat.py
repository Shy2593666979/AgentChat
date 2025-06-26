from pydantic import BaseModel, Field


class ConversationReq(BaseModel):
    use_input: str = Field(description="用户的问题")
    dialog_id: str = Field(description="对话的ID值")