# test_outcrawl_search.py
# 需要在配置文件中填写 tools.outcrawl.api_key，在 src/backend 目录运行：
#     uv run python -m tests.manual.test_outcrawl_search
import asyncio

from agentchat.settings import init_app_settings
from agentchat.tools.web_search.outcrawl_search.action import outcrawl_search


def run_test(name, **kwargs):
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = outcrawl_search.invoke(kwargs)
        print(result[:500] + "..." if len(result) > 500 else result)  # 截断长输出
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    asyncio.run(init_app_settings())

    # 测试 1: 基础搜索
    run_test(
        "基础搜索",
        query="人工智能最新进展",
        count=3
    )

    # 测试 2: 限定数量
    run_test(
        "限定数量",
        query="大模型 Agent 框架",
        count=2
    )

    # 测试 3: 极端关键词（预期可能无结果）
    run_test(
        "无结果测试",
        query="asdfghjkl123456789!@#",
        count=1
    )
