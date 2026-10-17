from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, Dict, List, Optional

from agentchat.database.dao.usage_stats import UsageStats, UsageStatsDao


class UsageStatsService:

    @classmethod
    async def create_usage_stats(cls, agent, model, user_id, input_tokens=0, output_tokens=0, conversation_id=None):
        usage_stats = UsageStats(
            agent=agent,
            model=model,
            user_id=user_id,
            conversation_id=conversation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        await UsageStatsDao.create_usage_stats(usage_stats)

    @classmethod
    def sync_create_usage_stats(cls, agent, model, user_id, input_tokens=0, output_tokens=0, conversation_id=None):
        usage_stats = UsageStats(
            agent=agent,
            model=model,
            user_id=user_id,
            conversation_id=conversation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        UsageStatsDao.sync_create_usage_stats(usage_stats)

    @classmethod
    async def get_usage_agents(cls, user_id) -> List[str]:
        agents = await UsageStatsDao.get_usage_agents(user_id)
        return agents

    @classmethod
    async def get_usage_models(cls, user_id) -> List[str]:
        models = await UsageStatsDao.get_usage_models(user_id)
        return models

    @classmethod
    async def get_usage_by_agent_model(
        cls,
        user_id: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        delta_days: int = 10000,  # 默认值可视为所有数据
        conversation_id: Optional[str] = None,
    ):
        results = await UsageStatsDao.get_agent_model_time_usage(
            user_id, agent, model, delta_days, conversation_id
        )
        # 按日期升序排序
        results.sort(key=lambda x: x.create_time.date() if x.create_time else datetime.min.date())

        # 初始化嵌套字典（默认结构：日期→{"agent": {}, "model": {}}）
        date_usage_dict: DefaultDict[str, Dict[str, Dict]] = defaultdict(
            lambda: {
                "agent": defaultdict(dict),
                "model": defaultdict(dict),
            }
        )

        # 遍历数据，填充字典
        for item in results:
            # 提取日期字符串（仅保留年-月-日，作为第一层key）
            date_key = item.create_time.date().isoformat() if item.create_time else "未知日期"

            # 处理agent相关统计
            agent_key = item.agent or "未指定agent"
            # 初始化agent的token数据
            if not date_usage_dict[date_key]["agent"][agent_key]:
                date_usage_dict[date_key]["agent"][agent_key] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                }
            # 累加agent的token数量
            date_usage_dict[date_key]["agent"][agent_key]["input_tokens"] += item.input_tokens
            date_usage_dict[date_key]["agent"][agent_key]["output_tokens"] += item.output_tokens
            date_usage_dict[date_key]["agent"][agent_key]["total_tokens"] += item.input_tokens + item.output_tokens

            # 处理model相关统计
            model_key = item.model or "未指定model"
            # 初始化model的token数据
            if not date_usage_dict[date_key]["model"][model_key]:
                date_usage_dict[date_key]["model"][model_key] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                }
            # 累加model的token数量
            date_usage_dict[date_key]["model"][model_key]["input_tokens"] += item.input_tokens
            date_usage_dict[date_key]["model"][model_key]["output_tokens"] += item.output_tokens
            date_usage_dict[date_key]["model"][model_key]["total_tokens"] += item.input_tokens + item.output_tokens

        final_dict = dict(date_usage_dict)
        return final_dict

    @classmethod
    async def get_usage_count_by_agent_model(
            cls,
            user_id: str,
            agent: Optional[str] = None,
            model: Optional[str] = None,
            delta_days: int = 10000,  # 默认值可视为所有数据
            conversation_id: Optional[str] = None,
    ):
        results = await UsageStatsDao.get_agent_model_time_usage(
            user_id, agent, model, delta_days, conversation_id
        )
        # 按日期升序排序
        results.sort(key=lambda x: x.create_time.date() if x.create_time else datetime.min.date())

        # 初始化嵌套字典（默认结构：日期→{"agent": {}, "model": {}}）
        date_usage_dict: DefaultDict[str, Dict[str, Dict]] = defaultdict(
            lambda: {
                "agent": defaultdict(int),
                "model": defaultdict(int),
            }
        )

        # 遍历数据，填充字典
        for item in results:
            # 提取日期字符串（仅保留年-月-日，作为第一层key）
            date_key = item.create_time.date().isoformat() if item.create_time else "未知日期"

            # 处理agent相关统计 - 统计调用次数
            agent_key = item.agent or "未指定agent"
            date_usage_dict[date_key]["agent"][agent_key] += 1

            # 处理model相关统计 - 统计调用次数
            model_key = item.model or "未指定model"
            date_usage_dict[date_key]["model"][model_key] += 1

        final_dict = dict(date_usage_dict)
        return final_dict

    @classmethod
    async def get_conversation_usage(cls, user_id: str, conversation_ids: List[str]):
        """批量汇总会话累计模型用量，不与历史文本的估算 token 相加。"""
        results = await UsageStatsDao.get_conversation_usage(user_id, conversation_ids)
        return {
            conversation_id: {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": int(input_tokens + output_tokens),
                "model_calls": int(model_calls),
                "usage_available": True,
            }
            for conversation_id, input_tokens, output_tokens, model_calls in results
        }
