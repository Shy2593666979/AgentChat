from enum import Enum
from pydantic import BaseModel


class UsageStatsRequest(BaseModel):
    agent: str = None
    model: str = None
    delta_days: int

class UsageStatsAgentType(str, Enum):
    mars_agent = "Mars-Agent"
    lingseek_agent = "LingSeek-Agent"
    simple_agent = "Simple-Agent"

