# test_youcom_research.py
from agentchat.tools.youcom_research.action import youcom_research


def run_test(name, **kwargs):
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = youcom_research(**kwargs)
        print(result[:800] + "..." if len(result) > 800 else result)
    except Exception as e:
        print(f"❌ 异常: {e}")


if __name__ == "__main__":
    # 测试 1: 标准研究深度（需配置 YOUCOM_API_KEY）
    run_test(
        "标准研究深度",
        query="大语言模型在医疗领域的应用",
        research_effort="standard",
    )

    # 测试 2: 快速研究
    run_test(
        "快速研究 lite",
        query="最新 AI Agent 框架对比",
        research_effort="lite",
    )

    # 测试 3: 深度研究
    run_test(
        "深度研究 deep",
        query="LangGraph 与 AutoGen 技术对比",
        research_effort="deep",
    )

    # 测试 4: 空查询
    run_test(
        "空查询",
        query="",
        research_effort="standard",
    )
