import os
from typing import Dict, List

from agentchat.services.deepsearch.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from tavily import TavilyClient
from loguru import logger
import json

from agentchat.services.deepsearch.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agentchat.services.deepsearch.configuration import Configuration
from agentchat.services.deepsearch.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from agentchat.core.models.manager import ModelManager

load_dotenv()

# 检查Tavily API密钥
if os.getenv("TAVILY_API_KEY") is None:
    raise ValueError("TAVILY_API_KEY is not set")

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# 节点
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph节点，根据用户问题生成搜索查询。

    使用本地LLM模型基于用户问题创建优化的网络研究搜索查询。

    参数:
        state: 包含用户问题的当前图状态
        config: 可运行的配置，包括LLM提供者设置

    返回:
        包含状态更新的字典，包括包含生成查询的search_query键
    """
    configurable = Configuration.from_runnable_config(config)

    # 检查自定义初始搜索查询计数
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # 使用ModelManager获取模型
    llm = ModelManager.get_conversation_model()

    # 格式化提示词
    current_date = get_current_date()
    research_topic = get_research_topic(state["messages"])
    
    formatted_prompt = f"""
    {query_writer_instructions.format(
        current_date=current_date,
        research_topic=research_topic,
        number_queries=state["initial_search_query_count"],
    )}
    
    请用JSON格式回复，包含以下两个键:
    {{
        "rationale": "简要解释这些查询与研究主题的相关性",
        "query": ["查询1", "查询2", ...]
    }}
    """
    
    # 生成搜索查询
    response = llm.invoke(formatted_prompt)
    content = response.content
    
    # 解析JSON响应
    try:
        result = json.loads(content)
        queries = result.get("query", [])
        if not queries:
            # 如果没有查询，使用原始研究主题作为查询
            queries = [research_topic]
        return {"search_query": queries}
    except:
        # 如果解析失败，使用原始研究主题作为查询
        logger.error("解析查询生成结果失败，使用原始问题作为查询")
        return {"search_query": [research_topic]}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph节点，将搜索查询发送到网络研究节点。

    用于为每个搜索查询生成n个网络研究节点。
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph节点，使用Tavily搜索API执行网络研究。

    执行网络搜索并格式化结果。

    参数:
        state: 包含搜索查询和ID的当前图状态
        config: 可运行的配置

    返回:
        包含状态更新的字典，包括sources_gathered和web_research_result
    """
    search_query = state["search_query"]
    query_id = state["id"]
    
    logger.info(f"🔍 执行搜索: {search_query}")
    
    try:
        # 使用Tavily执行搜索
        response = tavily_client.search(
            query=search_query,
            max_results=10,
            time_range="month",  # 时间跨度为近一月内的事情
            include_raw_content="markdown",
            country="china"
        )
        
        # 格式化搜索结果
        formatted_results = format_tavily_results(response)
        
        # 创建简单的引用标记
        sources = []
        for idx, result in enumerate(response.get("results", [])):
            source_id = f"{query_id}-{idx}"
            source_url = result.get("url", "")
            source_title = result.get("title", "未知标题")
            sources.append({
                "short_url": f"https://search.result/{source_id}",
                "value": source_url,
                "label": source_title
            })
        
        logger.info(f"✅ 找到 {len(response.get('results', []))} 个结果")
        
        return {
            "sources_gathered": sources,
            "search_query": [search_query],
            "web_research_result": [formatted_results],
        }
    
    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        return {
            "sources_gathered": [],
            "search_query": [search_query],
            "web_research_result": [f"搜索失败: {str(e)}"],
        }


def format_tavily_results(response: Dict) -> str:
    """格式化Tavily搜索结果"""
    if not response.get("results"):
        return "未找到相关结果"

    formatted = []
    for idx, result in enumerate(response["results"]):
        url = result.get("url", "")
        title = result.get("title", "")
        content = result.get("content", "")
        formatted.append(f"[{title}]({url})\n内容: {content}")

    return "\n\n".join(formatted)


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph节点，识别知识缺口并生成潜在的后续查询。

    分析当前摘要以识别进一步研究的领域，并生成潜在的后续查询。
    使用结构化输出以JSON格式提取后续查询。

    参数:
        state: 包含运行摘要和研究主题的当前图状态
        config: 可运行的配置，包括LLM提供者设置

    返回:
        包含状态更新的字典，包括包含生成的后续查询的search_query键
    """
    configurable = Configuration.from_runnable_config(config)
    # 增加研究循环计数
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    
    # 使用ModelManager获取模型
    llm = ModelManager.get_conversation_model()

    # 格式化提示词
    current_date = get_current_date()
    research_topic = get_research_topic(state["messages"])
    summaries = "\n\n---\n\n".join(state["web_research_result"])
    
    formatted_prompt = f"""
    {reflection_instructions.format(
        current_date=current_date,
        research_topic=research_topic,
        summaries=summaries,
    )}
    """
    
    # 生成反思结果
    response = llm.invoke(formatted_prompt)
    content = response.content
    
    # 解析JSON响应
    try:
        result = json.loads(content)
        is_sufficient = result.get("is_sufficient", True)
        knowledge_gap = result.get("knowledge_gap", "")
        follow_up_queries = result.get("follow_up_queries", [])
        
        logger.info(f"📊 反思结果: {'足够' if is_sufficient else '不足够'}")
        if not is_sufficient:
            logger.info(f"💭 知识缺口: {knowledge_gap}")
            logger.info(f"🔄 后续查询: {follow_up_queries}")
        
        return {
            "is_sufficient": is_sufficient,
            "knowledge_gap": knowledge_gap,
            "follow_up_queries": follow_up_queries,
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }
    except:
        logger.error("解析反思结果失败，默认为足够")
        return {
            "is_sufficient": True,
            "knowledge_gap": "",
            "follow_up_queries": [],
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph路由函数，确定研究流程中的下一步。

    通过决定是继续收集信息还是基于配置的最大研究循环数来完成摘要，控制研究循环。

    参数:
        state: 包含研究循环计数的当前图状态
        config: 可运行的配置，包括max_research_loops设置

    返回:
        指示要访问的下一个节点的字符串字面量或发送到web_research的查询列表
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        logger.info("✅ 研究完成，准备生成最终答案")
        return "finalize_answer"
    else:
        logger.info("🔄 继续研究，执行后续查询")
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph节点，完成研究摘要。

    通过去重和格式化源，然后将它们与运行摘要结合，创建一个结构良好的
    带有适当引用的研究报告，准备最终输出。

    参数:
        state: 包含运行摘要和收集的源的当前图状态

    返回:
        包含状态更新的字典，包括包含格式化最终摘要和源的running_summary键
    """
    # 使用ModelManager获取模型
    llm = ModelManager.get_conversation_model()

    # 格式化提示词
    current_date = get_current_date()
    research_topic = get_research_topic(state["messages"])
    summaries = "\n---\n\n".join(state["web_research_result"])
    
    formatted_prompt = f"""
    {answer_instructions.format(
        current_date=current_date,
        research_topic=research_topic,
        summaries=summaries,
    )}
    """
    
    # 生成最终答案
    response = llm.invoke(formatted_prompt)
    content = response.content
    
    logger.info("🎯 生成最终答案完成")
    
    # 将短URL替换为原始URL
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in content:
            content = content.replace(source["short_url"], source["value"])
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=content)],
        "sources_gathered": unique_sources,
    }


def get_research_topic(messages):
    """从消息中获取研究主题"""
    if not messages:
        return ""
    
    # 如果只有一条消息，直接返回内容
    if len(messages) == 1:
        return messages[-1].content
    
    # 否则，组合最近的用户消息
    for message in reversed(messages):
        if hasattr(message, 'type') and message.type == 'human':
            return message.content
        if hasattr(message, 'role') and message.role == 'user':
            return message.content
    
    # 如果没有找到用户消息，返回最后一条消息
    return messages[-1].content


# 创建我们的智能体图
builder = StateGraph(OverallState, config_schema=Configuration)

# 定义我们将循环的节点
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# 将入口点设置为`generate_query`
# 这意味着这个节点是第一个被调用的
builder.add_edge(START, "generate_query")
# 添加条件边以在并行分支中继续搜索查询
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# 对网络研究进行反思
builder.add_edge("web_research", "reflection")
# 评估研究
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# 完成答案
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")