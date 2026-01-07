from typing import List, Any
from pydantic import BaseModel

class AgentSkillFile(BaseModel):
    name: str
    path: str
    type: str = "file"
    content: str


class AgentSkillFolder(BaseModel):
    name: str
    path: str
    type: str = "folder"
    folder: List[Any] = []


class AgentSkillCreateReq(BaseModel):
    name: str
    description: str

class AgentSkillDeleteReq(BaseModel):
    agent_skill_id: str

class AgentSkillFileUpdateReq(BaseModel):
    path: str
    content: str
    agent_skill_id: str

class AgentSkillFileAddReq(BaseModel):
    path: str
    name: str
    agent_skill_id: str

class AgentSkillFileDeleteReq(BaseModel):
    path: str
    name: str
    agent_skill_id: str