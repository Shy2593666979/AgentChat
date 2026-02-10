# test_bocha_search_simple.py
from agentchat.tools.web_search.bocha_search.action import bocha_search

def run_test(name, **kwargs):
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = bocha_search(**kwargs)
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

    # 测试 2: 时间范围限制（一周内）
    run_test(
        "一周内结果",
        query="大模型 Agent 框架",
        freshness="oneWeek",
        count=2
    )

    # 测试 3: 包含摘要
    run_test(
        "带摘要搜索",
        query="LangChain 最佳实践",
        summary=True,
        count=2
    )

    # 测试 4: 限定特定网站
    run_test(
        "限定知乎",
        query="强化学习入门",
        include="zhihu.com",
        count=2
    )

    # 测试 5: 排除特定网站
    run_test(
        "排除 GitHub",
        query="开源项目",
        exclude="github.com",
        count=2
    )

    # 测试 6: 极端关键词（预期可能无结果）
    run_test(
        "无结果测试",
        query="asdfghjkl123456789!@#",
        count=1
    )