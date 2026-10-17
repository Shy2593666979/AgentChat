"""验证新用户默认资源的事务初始化、隔离与删除保留。"""
from contextlib import contextmanager
from copy import deepcopy
from unittest.mock import patch

import pytest
from agentchat.settings import app_settings
from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine, select

if not app_settings.database:
    app_settings.database = {
        "url": "sqlite:///:memory:",
    }

from agentchat.database.dao.user import UserDao
from agentchat.database.dao.user_resources import UserResourcesDao
from agentchat.database.models.agent import AgentTable
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.database.models.mcp_server import MCPServerTable
from agentchat.database.models.tool import ToolTable
from agentchat.database.models.user import UserTable


@pytest.fixture
def database(tmp_path):
    engine = create_engine(
        "sqlite:///" + (tmp_path / "private.db").as_posix(),
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(ToolTable(tool_id="tool-template", name="search", display_name="搜索", description="工具说明", user_id="0", logo_url=""))
        session.add(
            AgentSkill(
                id="skill-template",
                name="研究",
                description="技能说明",
                user_id="0",
                as_tool_name="research",
                folder={
                    "folder": [
                        {
                            "name": "SKILL.md",
                            "content": "原始内容",
                        }
                    ],
                },
            )
        )
        session.add(MCPServerTable(mcp_server_id="mcp-template", server_name="搜索服务", user_id="0", user_name="system", description="服务说明", mcp_as_tool_name="search_service", url="https://example.com/mcp", type="sse", logo_url="", config=[], tools=[], params=[]))
        session.add(AgentTable(id="agent-template", name="研究助手", user_id="0", logo_url="", llm_id="shared-model", tool_ids=["tool-template"], agent_skill_ids=["skill-template"], mcp_ids=["mcp-template"]))
        for user_id in ("1", "2"):
            user = UserTable(user_id=user_id, user_name="user-" + user_id, user_email="", user_avatar="", user_password="unused")
            session.add(user)
            session.flush()
            UserResourcesDao.create_defaults(session, user)
        session.commit()
    yield engine
    engine.dispose()


def owned(session, model, user_id):
    return session.exec(select(model).where(model.user_id == user_id)).all()


def test_independent_ids_deep_copy_and_deletions_survive_restart(database):
    SQLModel.metadata.create_all(database)
    models = (ToolTable, AgentSkill, MCPServerTable, AgentTable)
    with Session(database) as session:
        for model in models:
            first, second = owned(session, model, "1"), owned(session, model, "2")
            assert len(first) == len(second) == 1
            key = inspect(model).primary_key[0].name
            assert getattr(first[0], key) != getattr(second[0], key)
            assert len(owned(session, model, "0")) == 1
        agent = owned(session, AgentTable, "1")[0]
        assert agent.tool_ids == [owned(session, ToolTable, "1")[0].tool_id]
        assert agent.agent_skill_ids == [owned(session, AgentSkill, "1")[0].id]
        assert agent.mcp_ids == [owned(session, MCPServerTable, "1")[0].mcp_server_id]
        assert agent.llm_id == "shared-model"
        skill = owned(session, AgentSkill, "1")[0]
        folder = deepcopy(skill.folder)
        folder["folder"][0]["content"] = "个人修改"
        skill.folder = folder
        session.add(skill)
        owned(session, ToolTable, "1")[0].display_name = "个人工具"
        owned(session, MCPServerTable, "1")[0].url = "https://private.example.com/mcp"
        agent.name = "个人助手"
        session.commit()
    SQLModel.metadata.create_all(database)
    with Session(database) as session:
        assert owned(session, AgentSkill, "1")[0].folder["folder"][0]["content"] == "个人修改"
        for user_id in ("0", "2"):
            assert owned(session, AgentSkill, user_id)[0].folder["folder"][0]["content"] == "原始内容"
            assert owned(session, ToolTable, user_id)[0].display_name == "搜索"
            assert owned(session, MCPServerTable, user_id)[0].url == "https://example.com/mcp"
            assert owned(session, AgentTable, user_id)[0].name == "研究助手"
        for model in models:
            session.delete(owned(session, model, "1")[0])
        session.commit()
    SQLModel.metadata.create_all(database)
    with Session(database) as session:
        assert all(owned(session, model, "1") == [] for model in models)
        assert all(len(owned(session, model, "2")) == 1 for model in models)


def test_user_creation_is_atomic_with_resource_creation(database):
    @contextmanager
    def sessions():
        with Session(database) as session:
            yield session

    create_defaults = UserResourcesDao.create_defaults

    def failing(session, user):
        create_defaults(session, user)
        raise RuntimeError("模拟初始化失败")

    def new_user():
        return UserTable(user_id="new", user_name="new", user_avatar="", user_password="unused")

    with patch("agentchat.database.dao.user.session_getter", sessions):
        with patch.object(UserResourcesDao, "create_defaults", failing):
            with pytest.raises(RuntimeError):
                UserDao._save_new_user(new_user())
        with Session(database) as session:
            assert session.get(UserTable, "new") is None
            assert owned(session, ToolTable, "new") == []
        user = UserDao._save_new_user(new_user())
        assert user.user_id == "new"
        with Session(database) as session:
            assert len(owned(session, AgentTable, "new")) == 1
