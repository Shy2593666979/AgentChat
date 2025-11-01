from typing import List, Any
from pydantic import BaseModel


class LingSeekGuidePrompt(BaseModel):
    query: str
    web_search: bool = True
    plugins: List[str] = []
    mcp_servers: List[str] = []


class LingSeekGuidePromptFeedBack(BaseModel):
    query: str
    guide_prompt: str
    feedback: str = ""
    web_search: bool = True
    plugins: List[str] = []
    mcp_servers: List[str] = []

class LingSeekTask(BaseModel):
    query: str
    guide_prompt: str
    web_search: bool = True
    plugins: List[str] = []
    mcp_servers: List[str] = []

class LingSeekTaskStep(BaseModel):
    thought: str
    step_id: str
    title: str
    target: str
    workflow: Any
    precautions: str
    input_thought: str
    input: List[str] = []

    result: str = ""