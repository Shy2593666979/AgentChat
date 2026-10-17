# test_serply_search_simple.py
from agentchat.tools.web_search.serply_search.action import serply_search


def run_test(name, **kwargs):
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = serply_search(**kwargs)
        print(result[:500] + "..." if len(result) > 500 else result)  # 截断长输出
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
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
