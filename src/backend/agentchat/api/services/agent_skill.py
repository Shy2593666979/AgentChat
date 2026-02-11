from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.database.dao.agent_skill import AgentSkillDao
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.prompts.skill import AgentSkillAsToolPrompt
from agentchat.schema.agent_skill import AgentSkillCreateReq, AgentSkillFile, AgentSkillFolder, AgentSkillResponseFormat


def default_agent_skill_folder(name, description):
    default_skill_readme = f"""
---
name: {name}
description: {description}
---
    """

    default_folder = AgentSkillFolder(name=name, path=f"/{name}")
    default_folder.folder.append(AgentSkillFile(name="SKILL.md", path=f"/{name}/SKILL.md", content=default_skill_readme))
    default_folder.folder.append(AgentSkillFolder(name="reference", path=f"/{name}/reference"))
    default_folder.folder.append(AgentSkillFolder(name="scripts", path=f"/{name}/scripts"))

    return default_folder.model_dump()
    
class AgentSkillService:

    @classmethod
    async def create_agent_skill(cls, agent_skill_req: AgentSkillCreateReq, user_id):
        structured_agent = StructuredResponseAgent(AgentSkillResponseFormat)
        structured_response = structured_agent.get_structured_response(
            AgentSkillAsToolPrompt.format(
                name=agent_skill_req.name,
                description=agent_skill_req.description
            )
        )

        agent_skill = AgentSkill(
            **agent_skill_req.model_dump(),
            user_id=user_id,
            as_tool_name=structured_response.as_tool_name,
            folder=default_agent_skill_folder(agent_skill_req.name, agent_skill_req.description)
        )

        await AgentSkillDao.create_agent_skill(agent_skill)
        return agent_skill.model_dump()

    @classmethod
    async def delete_agent_skill(cls, agent_skill_id):
        return await AgentSkillDao.delete_agent_skill(agent_skill_id)

    @classmethod
    async def get_agent_skills(cls, user_id):
        results = await AgentSkillDao.get_agent_skills(user_id)
        return [result.to_dict() for result in results]

    @classmethod
    async def get_agent_skill_by_id(cls, agent_skill_id):
        result = await AgentSkillDao.get_agent_skill_by_id(agent_skill_id)
        return result.to_dict()

    @classmethod
    async def get_agent_skills_by_ids(cls, agent_skill_ids):
        results = await AgentSkillDao.get_agent_skills_by_ids(agent_skill_ids)
        return results

    @classmethod
    async def update_agent_skill_file(cls, agent_skill_id, target_path, new_content):
        agent_skill = await AgentSkillDao.get_agent_skill_by_id(agent_skill_id)
        agent_skill_copy = agent_skill.folder.copy()

        for item in agent_skill_copy.get("folder", []):
            if item["path"] == target_path:
                item["content"] = new_content
                break

            # 如果是 reference 或 scripts 目录，检查其子项
            if item.get("name") in ("reference", "scripts") and "folder" in item:
                for subitem in item["folder"]:
                    if subitem["path"] == target_path:
                        subitem["content"] = new_content

        agent_skill.folder = agent_skill_copy
        await AgentSkillDao.update_agent_skill(agent_skill)
        return agent_skill.model_dump()

    @classmethod
    async def add_agent_skill_file(cls, agent_skill_id, path, name):
        agent_skill = await AgentSkillDao.get_agent_skill_by_id(agent_skill_id)
        agent_skill_copy = agent_skill.folder.copy()

        for item in agent_skill_copy.get("folder", []):
            # path 匹配根目录下的某个目录（如 /Search-Skill/reference）
            if item["path"] == path:
                if "folder" not in item:
                    item["folder"] = []  # 确保有 folder 列表
                item["folder"].append({
                    "name": name,
                    "type": "file",
                    "path": f"{path.rstrip('/')}/{name}",
                    "content": ""
                })
                break

        agent_skill.folder = agent_skill_copy
        await AgentSkillDao.update_agent_skill(agent_skill)
        return agent_skill.model_dump()

    @classmethod
    async def upload_agent_skill_file(cls, agent_skill_id, path, name, content):
        agent_skill = await AgentSkillDao.get_agent_skill_by_id(agent_skill_id)
        agent_skill_copy = agent_skill.folder.copy()

        for item in agent_skill_copy.get("folder", []):
            # path 匹配根目录下的某个目录（如 /Search-Skill/reference）
            if item["path"] == path:
                if "folder" not in item:
                    item["folder"] = []  # 确保有 folder 列表
                item["folder"].append({
                    "name": name,
                    "type": "file",
                    "path": f"{path.rstrip('/')}/{name}",
                    "content": content
                })
                break

        agent_skill.folder = agent_skill_copy
        await AgentSkillDao.update_agent_skill(agent_skill)
        return agent_skill.model_dump()

    @classmethod
    async def delete_agent_skill_file(cls, agent_skill_id, path, name):
        agent_skill = await AgentSkillDao.get_agent_skill_by_id(agent_skill_id)
        agent_skill_copy = agent_skill.folder.copy()

        target_path = f"{path.rstrip('/')}/{name}"

        for item in agent_skill_copy.get("folder", []):
            if item.get("path") == path and "folder" in item:
                item["folder"] = [
                    f for f in item["folder"]
                    if f.get("path") != target_path
                ]
                break

        agent_skill.folder = agent_skill_copy
        await AgentSkillDao.update_agent_skill(agent_skill)
        return agent_skill.model_dump()

    @staticmethod
    def get_skill_md_content(data):
        """
        从给定的 JSON 数据中提取 SKILL.md 文件的 content。

        Args:
            data (dict): 解析后的 JSON 字典（不是字符串）

        Returns:
            str: SKILL.md 的内容，如果没找到则返回空字符串
        """
        folder = data.get("folder", [])
        for item in folder:
            if item.get("name") == "SKILL.md" and item.get("type") == "file":
                return item.get("content", "")
        return ""