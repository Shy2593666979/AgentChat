"""验证默认技能真实入库、可见性、文件读取与重复启动时的数据保留。"""
import json
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

from agentchat.settings import app_settings

app_settings.database = {
    "url": "sqlite:///:memory:",
}

from agentchat.database.dao.agent_skill import AgentSkillDao
from agentchat.database.init_data import (
    init_default_agent_skills,
    load_default_skill_configs,
)
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.schemas.agent_skill import AgentSkillFolder
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class DefaultSkillTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(lambda conn: AgentSkill.__table__.create(conn))
        sessions = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        @asynccontextmanager
        async def isolated_session():
            async with sessions() as session:
                yield session

        self.session_patch = patch("agentchat.database.dao.agent_skill.async_session_getter", isolated_session)
        self.session_patch.start()

    async def asyncTearDown(self):
        self.session_patch.stop()
        await self.engine.dispose()

    async def test_initialization_is_visible_and_preserves_edits_on_restart(self):
        await init_default_agent_skills()
        skills = await AgentSkillDao.get_agent_skills("0")
        self.assertEqual(len(skills), 6)
        self.assertTrue(all(skill.user_id == "0" for skill in skills))
        ids = {skill.id for skill in skills}
        target = skills[0]
        original_tool_name = target.as_tool_name
        target.name = "用户编辑后的技能"
        target.folder = {
            **target.folder,
            "folder": [
                {
                    "type": "file",
                    "name": "SKILL.md",
                    "path": target.folder["path"] + "/SKILL.md",
                    "content": "用户编辑后的正文",
                }
            ],
        }
        await AgentSkillDao.update_agent_skill(target)
        await init_default_agent_skills()
        skills = await AgentSkillDao.get_agent_skills("0")
        self.assertEqual({skill.id for skill in skills}, ids)
        saved = await AgentSkillDao.get_agent_skill_by_id(target.id)
        self.assertEqual(saved.name, "用户编辑后的技能")
        self.assertEqual(saved.folder["folder"][0]["content"], "用户编辑后的正文")
        self.assertEqual(saved.as_tool_name, original_tool_name)

    async def test_files_are_valid_for_editor_and_skill_agent(self):
        # 仅加载文件树，不初始化模型，也不调用外部服务。
        from agentchat.core.agents.skill_agent import SkillAgent
        for config in load_default_skill_configs():
            skill = AgentSkill(**config)
            AgentSkillFolder.model_validate(skill.folder)
            agent = SkillAgent(skill, "ordinary-user")
            agent.load_skill_folder(skill.folder)
            self.assertTrue(agent.get_skill_md())
            self.assertEqual(len(agent.list_files()), 4)
            for suffix in ("reference/output-template.md", "reference/review-checklist.md", "SOURCES.md"):
                self.assertTrue(agent.get_file_content(skill.folder["path"] + "/" + suffix))

    async def test_existing_system_tool_identifier_keeps_original_id(self):
        config = load_default_skill_configs()[0]
        config["id"] = "existing-system-skill"
        await AgentSkillDao.create_agent_skill(AgentSkill(**config))
        await init_default_agent_skills()
        skills = await AgentSkillDao.get_agent_skills("0")
        self.assertEqual(len(skills), 6)
        self.assertIn("existing-system-skill", {skill.id for skill in skills})

    async def test_invalid_config_does_not_partially_insert(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "default_skills.json").write_text(
                json.dumps(
                    [
                        {
                            "key": "../outside",
                            "name": "非法技能",
                            "as_tool_name": "invalid_skill",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                await init_default_agent_skills(root)
        self.assertEqual(await AgentSkillDao.get_agent_skills("0"), [])


if __name__ == "__main__":
    unittest.main()
