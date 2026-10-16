"""Isolated backend compatibility checks; never connect to the configured MySQL."""
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agentchat.settings import app_settings
from sqlalchemy import inspect, text
from sqlalchemy.dialects.mysql import dialect as mysql_dialect
from sqlmodel import Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

# Configure the isolated database before importing its package.
app_settings.database = {
    "url": "sqlite:///:memory:",
}
# Load all real table models against an isolated in-memory URL.
import agentchat.database as database
from agentchat.database.connection import (
    create_database_engines,
    engine_options,
    ensure_database,
    resolve_database_urls,
)
from agentchat.database.models.agent import AgentTable
from agentchat.database.models.agent_skill import AgentSkill
from agentchat.database.models.user import UserTable


@pytest.mark.parametrize("url,expected", [
    ("mysql://user:test@localhost/example", "mysql"),
    ("mysql+pymysql://user:test@localhost/example", "mysql"),
    ("mysql+aiomysql://user:test@localhost/example", "mysql"),
    ("sqlite:///data/example.db", "sqlite"),
    ("sqlite+aiosqlite:///data/example.db", "sqlite"),
    ("sqlite:///:memory:", "sqlite"),
])
def test_url_selects_both_drivers(url, expected, tmp_path):
    urls = resolve_database_urls(
        {
            "url": url,
        },
        tmp_path,
    )
    assert urls.dialect == expected
    assert urls.sync.drivername == expected + ("+pymysql" if expected == "mysql" else "+pysqlite")
    assert urls.async_.drivername == expected + ("+aiomysql" if expected == "mysql" else "+aiosqlite")
    assert urls.sync.database == urls.async_.database


def test_only_primary_url_controls_switch(tmp_path):
    urls = resolve_database_urls(
        {
            "endpoint": "sqlite:///nested/app.db",
            "async_endpoint": "mysql+aiomysql://user:test@localhost/old",
        },
        tmp_path,
    )
    assert urls.sync.database == (tmp_path / "nested/app.db").as_posix()
    assert "charset" not in engine_options(urls.sync)["connect_args"]


def test_default_relative_path_still_uses_backend_directory():
    urls = resolve_database_urls(
        {
            "url": "sqlite:///data/path-check.db",
        }
    )
    assert urls.sync.database == (Path(__file__).resolve().parents[1] / "data/path-check.db").as_posix()


@pytest.mark.parametrize("url", ["postgresql://user:test@localhost/db", "mysql://user:test@localhost", "sqlite://remote-host/db"])
def test_invalid_backend_configuration_fails_early(url):
    with pytest.raises(ValueError):
        resolve_database_urls(
            {
                "url": url,
            }
        )


def test_sync_and_async_memory_share_data():
    urls = resolve_database_urls(
        {
            "url": "sqlite:///:memory:",
        }
    )
    engine, async_engine = create_database_engines(urls)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE shared (value TEXT)"))
            connection.execute(text("INSERT INTO shared VALUES ('中文')"))
        async def verify():
            async with async_engine.connect() as connection:
                assert (await connection.execute(text("SELECT value FROM shared"))).scalar_one() == "中文"
        asyncio.run(verify())
    finally:
        asyncio.run(async_engine.dispose())
        engine.dispose()


def test_real_schema_json_timestamps_commit_and_rollback(tmp_path):
    urls = resolve_database_urls(
        {
            "url": "sqlite:///nested/app.db",
        },
        tmp_path,
    )
    ensure_database(urls.sync)
    engine, async_engine = create_database_engines(urls)
    try:
        SQLModel.metadata.create_all(engine)
        assert len(inspect(engine).get_table_names()) == len(SQLModel.metadata.tables) == 22
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
        with Session(engine) as session:
            session.add(UserTable(user_id="qa-user", user_name="数据库测试", user_email="", user_avatar="", user_password="test-only"))
            session.add(AgentTable(id="qa-agent", user_id="qa-user", name="中文助手", logo_url="", tool_ids=["search"], knowledge_ids=["文档"], update_time=datetime(2000, 1, 1)))
            session.commit()
        async def verify_async():
            async with AsyncSession(async_engine) as session:
                agent = await session.get(AgentTable, "qa-agent")
                assert agent.tool_ids == ["search"]
                assert agent.knowledge_ids == ["文档"]
                agent.description = "应回滚"
                await session.rollback()
            async with AsyncSession(async_engine) as session:
                agent = await session.get(AgentTable, "qa-agent")
                assert agent.description == ""
                agent.description = "异步修改"
                session.add(
                    AgentSkill(
                        id="qa-skill",
                        name="测试技能",
                        description="JSON 测试",
                        user_id="qa-user",
                        folder={
                            "name": "目录",
                            "children": [
                                {
                                    "name": "SKILL.md",
                                    "content": "你好",
                                }
                            ],
                        },
                    )
                )
                await session.commit()
        asyncio.run(verify_async())
        with Session(engine) as session:
            agent = session.get(AgentTable, "qa-agent")
            assert agent.description == "异步修改"
            assert agent.update_time.year != 2000
            expected = datetime.fromisoformat(session.exec(text("SELECT datetime('now', '+8 hours')")).scalar_one())
            assert abs((expected - agent.create_time).total_seconds()) < 30
            skill = session.get(AgentSkill, "qa-skill")
            assert skill.folder["children"][0]["content"] == "你好"
    finally:
        asyncio.run(async_engine.dispose())
        engine.dispose()
    reopened, async_reopened = create_database_engines(urls)
    try:
        with Session(reopened) as session:
            assert session.get(UserTable, "qa-user").user_name == "数据库测试"
    finally:
        asyncio.run(async_reopened.dispose())
        reopened.dispose()


def test_mysql_bootstrap_preserves_url_and_quotes_database(monkeypatch):
    import agentchat.database.connection as module
    fake = MagicMock()
    fake.dialect = mysql_dialect()
    created = []
    def create(url, **options):
        created.append((url, options))
        return fake
    monkeypatch.setattr(module, "create_engine", create)
    url = resolve_database_urls(
        {
            "url": "mysql://user:p%40ss%3Aword@localhost:3307/example?charset=utf8mb4",
        }
    ).sync.set(database="name`test")
    ensure_database(url)
    assert created[0][0].database is None
    assert created[0][0].password == "p@ss:word"
    assert created[0][0].port == 3307
    statement = fake.connect.return_value.__enter__.return_value.execute.call_args.args[0]
    assert "CREATE DATABASE IF NOT EXISTS" in str(statement)
    assert "`name``test`" in str(statement)
    assert created[0][1]["connect_args"]["init_command"] == "SET SESSION time_zone = '+08:00'"
    fake.dispose.assert_called_once()


def test_mysql_application_schema_compiles_without_connecting():
    code = """
from agentchat.settings import app_settings
app_settings.database = {'url': 'mysql://user:test@localhost/unused'}
import agentchat.database as db
from sqlmodel import SQLModel
from sqlalchemy.schema import CreateTable
assert db.engine.dialect.name == 'mysql'
assert db.async_engine.dialect.driver == 'aiomysql'
for table in SQLModel.metadata.tables.values():
    ddl = str(CreateTable(table).compile(db.engine))
    assert "datetime('now'" not in ddl
db.engine.dispose()
"""
    subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1], check=True, capture_output=True, text=True)


def test_text2sql_sqlite_inspection_and_query_error_recovery(tmp_path):
    from agentchat.core.agents.text2sql_agent import Text2SQLAgent
    url = resolve_database_urls(
        {
            "url": "sqlite:///report.db",
        },
        tmp_path,
    )
    engine, async_engine = create_database_engines(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE reports (id INTEGER PRIMARY KEY, title TEXT)"))
            connection.execute(text("INSERT INTO reports VALUES (1, '中文报表')"))
        agent = Text2SQLAgent(str(url.sync))
        try:
            assert "Database dialect: sqlite" in agent.schema_str
            assert "reports" in agent.schema_str
            assert agent._execute_sql("SELECT title FROM reports") == (
                [
                    {
                        "title": "中文报表",
                    }
                ],
                None,
            )
            assert agent._execute_sql("SELECT missing FROM reports")[1]
            assert agent._execute_sql("SELECT COUNT(*) AS n FROM reports")[0] == [
                {
                    "n": 1,
                }
            ]
            assert agent._execute_sql("DELETE FROM reports")[0] is None
            assert agent.client is None
        finally:
            agent.close()
        mysql_url = Text2SQLAgent.__new__(Text2SQLAgent)._get_database_url(
            {
                "user": "user",
                "password": "p@ss:word",
                "database": "example",
            }
        )
        assert mysql_url.password == "p@ss:word"
        assert mysql_url.drivername == "mysql+pymysql"
    finally:
        asyncio.run(async_engine.dispose())
        engine.dispose()


def test_existing_sync_and_async_daos_use_selected_sqlite():
    from agentchat.database.dao.agent import AgentDao
    from agentchat.database.dao.usage_stats import UsageStatsDao
    from agentchat.database.dao.user import UserDao
    from agentchat.database.models.usage_stats import UsageStats
    SQLModel.metadata.create_all(database.engine)
    with Session(database.engine) as session:
        session.add(UserTable(user_id="dao-user", user_name="DAO测试", user_email="", user_avatar="", user_password="test-only"))
        session.commit()
    assert UserDao.get_user_by_username("DAO测试").user_id == "dao-user"
    async def verify():
        await AgentDao.create_agent(AgentTable(id="dao-agent", name="DAO助手", user_id="dao-user", logo_url="", tool_ids=["search"]))
        agent = await AgentDao.select_agent_by_name("DAO助手")
        assert agent.tool_ids == ["search"]
        await UsageStatsDao.create_usage_stats(UsageStats(agent="DAO助手", model="test-model", user_id="dao-user", input_tokens=3, output_tokens=5))
        records = await UsageStatsDao.get_agent_model_time_usage("dao-user", delta_days=1)
        assert len(records) == 1
        assert records[0].input_tokens + records[0].output_tokens == 8
        await AgentDao.delete_agent_by_id("dao-agent")
        assert await AgentDao.select_agent_by_name("DAO助手") is None
    asyncio.run(verify())
