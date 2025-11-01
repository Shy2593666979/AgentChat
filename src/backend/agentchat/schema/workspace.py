from enum import Enum
from typing import List
from pydantic import BaseModel

class WorkSpaceAgents(Enum):
    LingSeekAgent: str = "lingseek"

    SimpleAgent: str = "simple"


class WorkSpaceSimpleTask(BaseModel):
    query: str
    model_id: str
    plugins: List[str] = []
    mcp_servers: List[str] = []