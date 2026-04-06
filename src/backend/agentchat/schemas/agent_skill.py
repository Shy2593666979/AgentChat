from typing import List, Any
from pydantic import BaseModel, Field

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

class AgentSkillResponseFormat(BaseModel):
    as_tool_name: str = Field(..., description="根据提供的信息生成一个Skill名称，要求是2-4个英文单词组成，用下划线_隔开，必须以skill结尾")