from typing import Optional
from enum import Enum
from pydantic import BaseModel
from agentchat.settings import app_settings

class UsageStatsRequest(BaseModel):
    agent: Optional[str] = None
    model: Optional[str] = None
    delta_days: int = 10000

class UsageStatsAgentType(str, Enum):
    mars_agent = "Mars-Agent"
    lingseek_agent = "LingSeek-Agent"
    simple_agent = "Simple-Agent"
    wechat_agent = "WeChat-Agent"


class UsageStatsModelType(str, Enum):
    tool_call_model = app_settings.multi_models.tool_call_model.model_name
    conversation_model = app_settings.multi_models.conversation_model.model_name

