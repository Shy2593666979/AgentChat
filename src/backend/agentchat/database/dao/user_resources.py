from copy import deepcopy
from uuid import uuid4

from sqlmodel import Session, select

from agentchat.database.models.agent import AgentTable
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.database.models.mcp_server import MCPServerTable
from agentchat.database.models.tool import ToolTable
from agentchat.database.models.user import SystemUser, UserTable


class UserResourcesDao:
    @staticmethod
    def create_defaults(session: Session, user: UserTable):
        """为新用户复制默认资源，由调用方统一提交账号和资源。"""
        if user.user_id == SystemUser:
            return

        mappings = {}
        # 先复制依赖资源，再将智能体绑定指向当前用户的副本。
        for model, primary_key in (
            (ToolTable, "tool_id"),
            (AgentSkill, "id"),
            (MCPServerTable, "mcp_server_id"),
            (AgentTable, "id"),
        ):
            templates = session.exec(select(model).where(model.user_id == SystemUser)).all()
            if not templates:
                raise ValueError(f"默认资源模板尚未就绪：{model.__tablename__}")

            mapping = {}
            for template in templates:
                source_id = getattr(template, primary_key)
                target_id = uuid4().hex
                mapping[source_id] = target_id
                values = deepcopy(
                    template.model_dump(exclude={primary_key, "create_time", "update_time"})
                )
                values[primary_key] = target_id
                values["user_id"] = user.user_id
                if model is MCPServerTable:
                    values["user_name"] = user.user_name
                if model is AgentTable:
                    for field, resource in (
                        ("tool_ids", ToolTable),
                        ("agent_skill_ids", AgentSkill),
                        ("mcp_ids", MCPServerTable),
                    ):
                        values[field] = [
                            mappings[resource][identity]
                            for identity in values[field] or []
                            if identity in mappings[resource]
                        ]
                    # 默认智能体不继承任何用户知识库绑定。
                    values["knowledge_ids"] = []
                session.add(model(**values))
            session.flush()
            mappings[model] = mapping
