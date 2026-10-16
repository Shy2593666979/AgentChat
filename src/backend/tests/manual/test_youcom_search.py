# test_youcom_search.py
from agentchat.tools.youcom_search.action import youcom_search


def run_test(name, **kwargs):
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = youcom_search(**kwargs)
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"❌ 异常: {e}")


if __name__ == "__main__":
    # 测试 1: 基础搜索（需配置 YOUCOM_API_KEY）
    run_test(
        "基础搜索",
        query="人工智能最新进展",
        max_results=3,
    )

    # 测试 2: 大结果数量
    run_test(
        "更多结果",
        query="LangChain Agent 框架",
        max_results=5,
    )

    # 测试 3: 空查询
    run_test(
        "空查询",
        query="",
        max_results=3,
    )
