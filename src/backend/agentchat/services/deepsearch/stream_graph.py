import asyncio
from typing import Dict, List, AsyncGenerator, Optional, Callable
import contextvars
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from tavily import TavilyClient
from loguru import logger
import json
from dataclasses import dataclass

from agentchat.core.models.manager import ModelManager
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
from agentchat.settings import app_settings

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=app_settings.tools.tavily["api_key"])

# 使用contextvars来传递流式输出回调，支持并发
stream_callback: contextvars.ContextVar[Optional[Callable]] = contextvars.ContextVar('stream_callback', default=None)


@dataclass
class StreamOutput:
    """流式输出数据结构"""
    type: str  # streaming, start, complete, error, info
    node: str
    content: str
    metadata: Optional[Dict] = None


async def stream_output(node_name: str, content: str, output_type: str = "content", metadata: Optional[Dict] = None):
    """发送流式输出"""
    callback = stream_callback.get()
    if callback:
        try:
            output = StreamOutput(
                type=output_type,
                node=node_name,
                content=content,
                metadata=metadata or {}
            )
            await callback(output)
        except Exception as e:
            logger.error(f"流式输出回调失败: {e}")


class StreamingGraph:
    """流式输出的智能体类，每个实例独立管理自己的流式输出"""

    def __init__(self):
        self.output_queue = asyncio.Queue()
        self.conversation_model = ModelManager.get_conversation_model()

    async def _stream_callback(self, output: StreamOutput):
        """内部流式输出回调"""
        try:
            await self.output_queue.put({
                "type": output.type,
                "node": output.node,
                "content": output.content,
                "metadata": output.metadata
            })
        except asyncio.QueueFull:
            logger.warning("流式输出队列已满，丢弃输出")

    async def generate_query(self, state: OverallState, config: RunnableConfig) -> QueryGenerationState:
        """LangGraph节点，根据用户问题生成搜索查询。"""
        configurable = Configuration.from_runnable_config(config)

        if state.get("initial_search_query_count") is None:
            state["initial_search_query_count"] = configurable.number_of_initial_queries

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

        await stream_output("generate_query", f"开始生成搜索查询，主题：{research_topic}", "start")

        content = ""
        async for chunk in self.conversation_model.astream(formatted_prompt):
            content += chunk.content
        
        try:
            content = content.replace("```json", "").replace("```", "")
            result = json.loads(content)
            queries = result.get("query", [])
            if not queries:
                queries = [research_topic]

            await stream_output("generate_query", f"生成了{len(queries)}个搜索查询", "complete", {"queries": queries})
            return {"search_query": queries}
        except Exception as e:
            logger.error(f"解析查询生成结果失败: {e}")
            await stream_output("generate_query", "解析失败，使用原始问题作为查询", "error")
            return {"search_query": [research_topic]}

    def continue_to_web_research(self, state: QueryGenerationState):
        """LangGraph节点，将搜索查询发送到网络研究节点。"""
        return [
            Send("web_research", {"search_query": search_query, "id": int(idx)})
            for idx, search_query in enumerate(state["search_query"])
        ]

    async def web_research(self, state: WebSearchState, config: RunnableConfig) -> OverallState:
        """LangGraph节点，使用Tavily搜索API执行网络研究。"""
        search_query = state["search_query"]
        query_id = state["id"]

        await stream_output("web_research", f"开始搜索：{search_query}", "start",
                      {"query_id": query_id})
        logger.info(f"🔍 执行搜索: {search_query}")

        try:
            response = await asyncio.to_thread(
                tavily_client.search,
                query=search_query,
                max_results=10,
                time_range="month",
                include_raw_content="markdown",
                country="china"
            )
            
            formatted_results = self.format_tavily_results(response)

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

            result_count = len(response.get('results', []))
            await stream_output("web_research", f"找到 {result_count} 个搜索结果", "complete",
                          {"result_count": result_count, "query_id": query_id})
            logger.info(f"✅ 找到 {result_count} 个结果")

            return {
                "sources_gathered": sources,
                "search_query": [search_query],
                "web_research_result": [formatted_results],
            }
        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            await stream_output("web_research", error_msg, "error", {"query_id": query_id})
            logger.error(f"❌ {error_msg}")
            return {
                "sources_gathered": [],
                "search_query": [search_query],
                "web_research_result": [error_msg],
            }

    def format_tavily_results(self, response: Dict) -> str:
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

    async def reflection(self, state: OverallState, config: RunnableConfig) -> ReflectionState:
        """LangGraph节点，识别知识缺口并生成潜在的后续查询。"""
        configurable = Configuration.from_runnable_config(config)
        state["research_loop_count"] = state.get("research_loop_count", 0) + 1

        await stream_output("reflection", "开始分析研究结果，识别知识缺口", "start",
                      {"loop_count": state["research_loop_count"]})

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

        response = await self.conversation_model.ainvoke(formatted_prompt)
        content = response.content

        try:
            content = content.replace("```json", "").replace("```", "")
            result = json.loads(content)
            is_sufficient = result.get("is_sufficient", True)
            knowledge_gap = result.get("knowledge_gap", "")
            follow_up_queries = result.get("follow_up_queries", [])

            status = "足够" if is_sufficient else "不足够"
            await stream_output("reflection", f"分析完成：当前信息{status}", "complete",
                          {"is_sufficient": is_sufficient, "follow_up_count": len(follow_up_queries)})

            logger.info(f"📊 反思结果: {status}")
            if not is_sufficient:
                logger.info(f"💭 知识缺口: {knowledge_gap}")
                logger.info(f"🔄 后续查询: {follow_up_queries}")
                await stream_output("reflection", f"需要进行{len(follow_up_queries)}个后续查询", "info")

            return {
                "is_sufficient": is_sufficient,
                "knowledge_gap": knowledge_gap,
                "follow_up_queries": follow_up_queries,
                "research_loop_count": state["research_loop_count"],
                "number_of_ran_queries": len(state["search_query"]),
            }
        except Exception as e:
            logger.error(f"解析反思结果失败: {e}")
            await stream_output("reflection", "解析反思结果失败，默认为足够", "error")
            return {
                "is_sufficient": True,
                "knowledge_gap": "",
                "follow_up_queries": [],
                "research_loop_count": state["research_loop_count"],
                "number_of_ran_queries": len(state["search_query"]),
            }

    def evaluate_research(self, state: ReflectionState, config: RunnableConfig) -> OverallState:
        """LangGraph路由函数，确定研究流程中的下一步。"""
        configurable = Configuration.from_runnable_config(config)
        max_research_loops = (
            state.get("max_research_loops")
            if state.get("max_research_loops") is not None
            else configurable.max_research_loops
        )

        if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
            stream_output("evaluate_research", "研究完成，准备生成最终答案", "complete")
            logger.info("✅ 研究完成，准备生成最终答案")
            return "finalize_answer"
        else:
            stream_output("evaluate_research", "继续研究，执行后续查询", "continue")
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

    async def finalize_answer(self, state: OverallState, config: RunnableConfig):
        """LangGraph节点，完成研究摘要。"""
        await stream_output("finalize_answer", "开始生成最终答案\n", "start")

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

        content = ""
        async for chunk in self.conversation_model.astream(formatted_prompt):
            content += chunk.content
            await stream_output("finalize_answer", chunk.content, "streaming")

        logger.info("🎯 生成最终答案完成")
        await stream_output("finalize_answer", "最终答案生成完成", "complete")

        unique_sources = []
        for source in state["sources_gathered"]:
            if source["short_url"] in content:
                content = content.replace(source["short_url"], source["value"])
                unique_sources.append(source)

        return {
            "messages": [AIMessage(content=content)],
            "sources_gathered": unique_sources,
        }

    def create_graph(self) -> StateGraph:
        """创建LangGraph"""
        builder = StateGraph(OverallState, config_schema=Configuration)

        builder.add_node("generate_query", self.generate_query)
        builder.add_node("web_research", self.web_research)
        builder.add_node("reflection", self.reflection)
        builder.add_node("finalize_answer", self.finalize_answer)

        builder.add_edge(START, "generate_query")
        builder.add_conditional_edges(
            "generate_query", self.continue_to_web_research, ["web_research"]
        )
        builder.add_edge("web_research", "reflection")
        builder.add_conditional_edges(
            "reflection", self.evaluate_research, ["web_research", "finalize_answer"]
        )
        builder.add_edge("finalize_answer", END)

        return builder.compile(name="pro-search-agent")

    async def run_with_streaming(self, messages: List[HumanMessage]) -> AsyncGenerator[Dict, None]:
        """使用异步流式输出运行智能体"""
        graph = self.create_graph()
        
        async def graph_task():
            token = stream_callback.set(self._stream_callback)
            try:
                # 使用 astream 异步流式调用
                async for chunk in graph.astream({"messages": messages}):
                    # astream 已经将每个节点的输出流式化，
                    # 我们可以通过回调把它们送到队列
                    pass # astream本身就会触发节点中的stream_output
            except Exception as e:
                logger.error(f"图执行失败: {e}")
                await self._stream_callback(StreamOutput("error", "system", f"执行出错: {e}"))
            finally:
                await self._stream_callback(StreamOutput("end", "system", "执行完成"))
                stream_callback.reset(token)

        # 启动图执行任务
        task = asyncio.create_task(graph_task())

        # 从队列中异步地yield输出
        while True:
            output = await self.output_queue.get()
            yield output
            if output.get("type") == "end":
                break
        
        await task


def get_research_topic(messages):
    """从消息中获取研究主题"""
    if not messages:
        return ""

    if len(messages) == 1:
        return messages[-1].content

    for message in reversed(messages):
        if hasattr(message, 'type') and message.type == 'human':
            return message.content
        if hasattr(message, 'role') and message.role == 'user':
            return message.content

    return messages[-1].content


# 测试代码
async def main():
    agent = StreamingGraph()
    queries = ["搜索上海天气", "搜索深圳天气"]
    for i, query in enumerate(queries, 1):
        print(f"\n--- 第{i}次查询: {query} ---")
        user_msg = HumanMessage(content=query)
        
        async for output in agent.run_with_streaming([user_msg]):
            output_type = output.get('type', 'unknown')
            node = output.get('node', 'unknown')
            content = output.get('content', '')

            if output_type == "streaming":
                print(f"{content}", end='', flush=True)
            elif output_type in ["start", "complete", "error"]:
                emoji = {"start": "🚀", "complete": "✅", "error": "❌"}[output_type]
                print(f"\n{emoji} [{node}] {content}")
            elif output_type == "final_result":
                print(f"\n🎯 查询{i}完成")
            
            if output_type == 'end':
                break

if __name__ == "__main__":
    asyncio.run(main())