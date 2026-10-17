import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

from agentchat.settings import app_settings

app_settings.database = {
    "url": "sqlite:///:memory:",
}
app_settings.multi_models = SimpleNamespace(chat_model=SimpleNamespace(
    model_name="test-model", api_key="test-key", base_url="https://example.com/v1"))
from agentchat.api.services.agent import AgentService
from agentchat.api.services.agent_skill import AgentSkillService
from agentchat.api.services.tool import ToolService
from agentchat.database.dao.agent import AgentDao
from agentchat.database.dao.agent_skill import AgentSkillDao
from agentchat.database.dao.mcp_server import MCPServerDao
from agentchat.database.dao.tool import ToolDao

# 权限检查不连接对象存储、Redis 或外部模型。
user_stub = ModuleType("agentchat.api.services.user")
user_stub.UserService = object
user_stub.UserPayload = SimpleNamespace
async def stub_login_user():
    return SimpleNamespace(user_id="ordinary")
user_stub.get_login_user = stub_login_user
with patch.dict(
    "sys.modules",
    {
        "agentchat.api.services.user": user_stub,
    },
):
    from agentchat.api.services.mcp_server import MCPService
    from agentchat.api.v1 import agent_skill as routes
from agentchat.schemas.agent_skill import (
    AgentSkillDeleteReq,
    AgentSkillFileAddReq,
    AgentSkillFileDeleteReq,
    AgentSkillFileUpdateReq,
    AgentSkillUpdateReq,
)


class DefaultResourceTests(unittest.IsolatedAsyncioTestCase):
    checks = [
        (AgentService.verify_user_permission, AgentDao, "get_agent_user_id"),
        (ToolService.verify_user_permission, ToolDao, "get_tool_by_id"),
        (MCPService.verify_user_permission, MCPServerDao, "get_mcp_server_from_id"),
        (AgentSkillService.verify_user_permission, AgentSkillDao, "get_agent_skill_by_id"),
    ]

    async def test_only_owner_can_manage_resources_including_defaults(self):
        for check, dao, target in self.checks:
            for owner, caller, allowed in [("0", "ordinary", False), ("ordinary", "ordinary", True), ("private", "1", False), ("private", "ordinary", False)]:
                with self.subTest(service=target, owner=owner, caller=caller), patch.object(dao, target, AsyncMock(return_value=SimpleNamespace(user_id=owner, tool_id="resource"))):
                    if allowed:
                        await check("resource", caller)
                    else:
                        with self.assertRaises(ValueError):
                            await check("resource", caller)

    async def test_tool_permission_uses_owner_not_tool_id(self):
        with patch("agentchat.api.services.tool.ToolDao.get_tool_by_id", AsyncMock(return_value=SimpleNamespace(user_id="owner", tool_id="different-id"))):
            self.assertEqual(await ToolService._get_user_by_tool_id("different-id"), "owner")

    async def test_missing_resource_rejected(self):
        for check, dao, target in self.checks:
            with patch.object(dao, target, AsyncMock(return_value=None)), self.assertRaises(ValueError):
                await check("missing", "ordinary")

    async def test_skill_routes_authorize_before_mutation(self):
        cases = [
            (routes.delete_agent_skill, AgentSkillDeleteReq(agent_skill_id="private"), "delete_agent_skill"),
            (routes.update_agent_skill_file, AgentSkillFileUpdateReq(agent_skill_id="private", path="/x/SKILL.md", content="x"), "update_agent_skill_file"),
            (routes.add_agent_skill_file, AgentSkillFileAddReq(agent_skill_id="private", path="/x/scripts", name="x.py"), "add_agent_skill_file"),
            (routes.delete_agent_skill_file, AgentSkillFileDeleteReq(agent_skill_id="private", path="/x/scripts", name="x.py"), "delete_agent_skill_file"),
            (routes.update_agent_skill, AgentSkillUpdateReq(agent_skill_id="private", name="changed", description="changed"), "update_agent_skill_info"),
        ]
        for endpoint, req, mutation in cases:
            with patch.object(AgentSkillService, "verify_user_permission", AsyncMock(side_effect=ValueError("denied"))), patch.object(AgentSkillService, mutation, AsyncMock()) as writer:
                result = await endpoint(req, SimpleNamespace(user_id="ordinary"))
                writer.assert_not_awaited()
                self.assertEqual(result.status_code, 500)

    async def test_skill_metadata_preserves_paths_and_tool_identity(self):
        skill = SimpleNamespace(
            name="old",
            description="old",
            folder={
                "path": "/old",
                "folder": [],
            },
            as_tool_name="stable",
        )
        skill.to_dict = lambda: dict(
            name=skill.name,
            description=skill.description,
            folder=skill.folder,
            as_tool_name=skill.as_tool_name,
        )
        with patch("agentchat.api.services.agent_skill.AgentSkillDao.get_agent_skill_by_id", AsyncMock(return_value=skill)), patch("agentchat.api.services.agent_skill.AgentSkillDao.update_agent_skill", AsyncMock(return_value=skill)):
            result = await AgentSkillService.update_agent_skill_info("default", "new", "new description")
            self.assertEqual(result["name"], "new")
            self.assertEqual(result["folder"]["path"], "/old")
            self.assertEqual(result["as_tool_name"], "stable")

    async def test_default_skill_round_trip_and_deletion_in_isolated_database(self):
        from contextlib import asynccontextmanager

        from agentchat.database.dao.agent_skill import AgentSkillDao
        from agentchat.database.models.agent_skill import AgentSkill
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(lambda conn: AgentSkill.__table__.create(conn))
        sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        @asynccontextmanager
        async def test_session():
            async with sessions() as session:
                yield session

        try:
            with patch("agentchat.database.dao.agent_skill.async_session_getter", test_session):
                skill = await AgentSkillDao.create_agent_skill(
                    AgentSkill(
                        name="default",
                        description="original",
                        user_id="0",
                        as_tool_name="stable",
                        folder={
                            "name": "default",
                            "path": "/default",
                            "type": "folder",
                            "folder": [
                                {
                                    "name": "SKILL.md",
                                    "path": "/default/SKILL.md",
                                    "type": "file",
                                    "content": "original",
                                },
                                {
                                    "name": "scripts",
                                    "path": "/default/scripts",
                                    "type": "folder",
                                    "folder": [],
                                },
                            ],
                        },
                    )
                )
                visible = await AgentSkillDao.get_agent_skills("ordinary")
                self.assertEqual(visible, [])
                with self.assertRaises(ValueError):
                    await AgentSkillService.verify_user_permission(skill.id, "ordinary")
                # 用个人副本验证编辑与删除，不操作系统模板。
                skill.user_id = "ordinary"
                skill = await AgentSkillDao.update_agent_skill(skill)
                await AgentSkillService.verify_user_permission(skill.id, "ordinary")
                await AgentSkillService.update_agent_skill_info(skill.id, "edited", "edited description")
                await AgentSkillService.update_agent_skill_file(skill.id, "/default/SKILL.md", "edited content")
                saved = await AgentSkillDao.get_agent_skill_by_id(skill.id)
                self.assertEqual(saved.folder["folder"][0]["content"], "edited content")
                self.assertEqual(saved.name, "edited")
                await AgentSkillService.add_agent_skill_file(skill.id, "/default/scripts", "test.py")
                saved = await AgentSkillDao.get_agent_skill_by_id(skill.id)
                self.assertEqual(saved.folder["folder"][1]["folder"][0]["name"], "test.py")
                await AgentSkillService.delete_agent_skill_file(skill.id, "/default/scripts", "test.py")
                saved = await AgentSkillDao.get_agent_skill_by_id(skill.id)
                self.assertEqual(saved.folder["folder"][1]["folder"], [])
                await AgentSkillService.delete_agent_skill(skill.id)
                self.assertIsNone(await AgentSkillDao.get_agent_skill_by_id(skill.id))
        finally:
            await engine.dispose()
