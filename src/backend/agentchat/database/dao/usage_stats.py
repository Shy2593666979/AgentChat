from typing import Optional, List
from sqlmodel import select, and_
from datetime import datetime, timedelta
from agentchat.database.session import async_session_getter, session_getter
from agentchat.database.models.usage_stats import UsageStats


class UsageStatsDao:

    @classmethod
    async def create_usage_stats(cls, usage_stats: UsageStats):
        async with async_session_getter() as session:
            session.add(usage_stats)
            await session.commit()
            await session.refresh(usage_stats)
            return usage_stats

    @classmethod
    def sync_create_usage_stats(cls, usage_stats: UsageStats):
        with session_getter() as session:
            session.add(usage_stats)
            session.commit()
            session.refresh(usage_stats)
            return usage_stats

    @classmethod
    async def get_agent_all_usage(cls, user_id, agent):
        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.user_id == user_id,
                UsageStats.agent == agent
            )

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_monthly_usage(cls, user_id, agent):
        one_month_ago = datetime.now() - timedelta(days=30)
        current_time = datetime.now()

        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.agent == agent,
                UsageStats.user_id == user_id,
                UsageStats.create_time >= one_month_ago,
                UsageStats.create_time <= current_time
            )

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_weekly_usage(cls, user_id, agent):
        one_week_ago = datetime.now() - timedelta(days=7)
        current_time = datetime.now()

        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.agent == agent,
                UsageStats.user_id == user_id,
                UsageStats.create_time >= one_week_ago,
                UsageStats.create_time <= current_time
            )

            result = await session.exec(statement)
            return result.all()

    # 根据模型进行分类
    @classmethod
    async def get_model_all_usage(cls, user_id, model):
        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.user_id == user_id,
                UsageStats.model == model
            )

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_model_monthly_usage(cls, user_id, model):
        one_month_ago = datetime.now() - timedelta(days=30)
        current_time = datetime.now()

        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.model == model,
                UsageStats.user_id == user_id,
                UsageStats.create_time >= one_month_ago,
                UsageStats.create_time <= current_time
            )

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_model_weekly_usage(cls, user_id, model):
        one_week_ago = datetime.now() - timedelta(days=7)
        current_time = datetime.now()

        async with async_session_getter() as session:
            statement = select(UsageStats).where(
                UsageStats.model == model,
                UsageStats.user_id == user_id,
                UsageStats.create_time >= one_week_ago,
                UsageStats.create_time <= current_time
            )

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_model_time_usage(
        cls,
        user_id: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        delta_days: int = 10000 # 默认值可视为所有数据
    ):
        ago_time = datetime.now() - timedelta(days=delta_days)

        conditions = [
            UsageStats.user_id == user_id,
            UsageStats.create_time >= ago_time
        ]

        # 追加条件（根据agent和model是否存在）
        if agent is not None:
            conditions.append(UsageStats.agent == agent)
        if model is not None:
            conditions.append(UsageStats.model == model)

        statement = select(UsageStats).where(*conditions)

        async with async_session_getter() as session:
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_usage_agents(cls, user_id):
        async with async_session_getter() as session:
            statement = select(UsageStats.agent).where(
                UsageStats.user_id == user_id
            ).distinct()

            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_usage_models(cls, user_id):
        async with async_session_getter() as session:
            statement = select(UsageStats.model).where(
                UsageStats.user_id == user_id
            ).distinct()

            result = await session.exec(statement)
            return result.all()