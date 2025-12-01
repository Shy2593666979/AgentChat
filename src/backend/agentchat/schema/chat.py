from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ConversationReq(BaseModel):
    user_input: str = Field(description="用户的问题")
    dialog_id: str = Field(description="对话的ID值")
    file_url: Optional[str] = Field(None, description="对话中上传的文件的oss链接")


class ToolCall(BaseModel):
    tool_name: str = Field(..., description="工具名称（如 get_current_time、get_weather）")
    tool_args: Any = Field(..., description="工具参数（可字符串/字典/无参数，根据工具灵活定义）")
    message: str = Field(..., description="该工具调用的说明信息")

StepTools = List[ToolCall]

class PlanToolFlow(BaseModel):
    # 动态键名（step_1、step_2...），值为步骤对应的工具列表
    root: Dict[str, StepTools] = Field(
        ...,
        description="工具调用流程，键为步骤名（step_1/step_2...），值为该步骤的工具调用列表"
    )

    def dict(self, **kwargs) -> Dict[str, Any]:
        return super().dict(** kwargs)

    def model_dump(self, **kwargs):
        return super().model_dump(**kwargs)