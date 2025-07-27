import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """智能体的配置。"""

    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "用于智能体查询生成的语言模型名称。"
        },
    )

    reflection_model: str = Field(
        default="gemini-2.5-flash",
        metadata={
            "description": "用于智能体反思的语言模型名称。"
        },
    )

    answer_model: str = Field(
        default="gemini-2.5-pro",
        metadata={
            "description": "用于智能体回答的语言模型名称。"
        },
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "要生成的初始搜索查询数量。"},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "要执行的最大研究循环数量。"},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建一个Configuration实例。"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # 从环境或配置获取原始值
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # 过滤掉None值
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)