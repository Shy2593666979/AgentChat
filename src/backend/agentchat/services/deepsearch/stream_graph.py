from typing import Dict, List, Generator, Iterator, Optional, Callable
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
import queue
import threading
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
tavily_client = TavilyClient(api_key=app_settings.tool_tavily["api_key"])

# 使用contextvars来传递流式输出回调，支持并发
stream_callback: contextvars.ContextVar[Optional[Callable]] = contextvars.ContextVar('stream_callback', default=None)


@dataclass
class StreamOutput:
    """流式输出数据结构"""
    type: str  # streaming, start, complete, error, info
    node: str
    content: str
    metadata: Optional[Dict] = None


def stream_output(node_name: str, content: str, output_type: str = "content", metadata: Optional[Dict] = None):
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
            callback(output)
        except Exception as e:
            logger.error(f"流式输出回调失败: {e}")


class StreamingGraph:
    """流式输出的智能体类，每个实例独立管理自己的流式输出"""

    def __init__(self):
        self.output_queue = queue.Queue()
        self.is_running = False
        self.conversation_model = ModelManager.get_conversation_model()

    def _stream_callback(self, output: StreamOutput):
        """内部流式输出回调"""
        try:
            self.output_queue.put_nowait({
                "type": output.type,
                "node": output.node,
                "content": output.content,
                "metadata": output.metadata
            })
        except queue.Full:
            logger.warning("流式输出队列已满，丢弃输出")

    def generate_query(self, state: OverallState, config: RunnableConfig) -> QueryGenerationState:
        """LangGraph节点，根据用户问题生成搜索查询。"""
        configurable = Configuration.from_runnable_config(config)

        # 检查自定义初始搜索查询计数
        if state.get("initial_search_query_count") is None:
            state["initial_search_query_count"] = configurable.number_of_initial_queries

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

        # 发送开始信号
        stream_output("generate_query", f"开始生成搜索查询，主题：{research_topic}", "start")

        # 生成搜索查询
        content = ""
        for chunk in self.conversation_model.stream(formatted_prompt):
            content += chunk.content
            # 流式输出每个chunk
            # stream_output("generate_query", chunk.content, "streaming")

        # 解析JSON响应
        try:
            content.replace("```json", "").replace("```", "")
            result = json.loads(content)
            queries = result.get("query", [])
            if not queries:
                queries = [research_topic]

            # 发送完成信号
            stream_output("generate_query", f"生成了{len(queries)}个搜索查询", "complete", {"queries": queries})
            return {"search_query": queries}
        except Exception as e:
            logger.error(f"解析查询生成结果失败: {e}")
            stream_output("generate_query", "解析失败，使用原始问题作为查询", "error")
            return {"search_query": [research_topic]}

    def continue_to_web_research(self, state: QueryGenerationState):
        """LangGraph节点，将搜索查询发送到网络研究节点。"""
        return [
            Send("web_research", {"search_query": search_query, "id": int(idx)})
            for idx, search_query in enumerate(state["search_query"])
        ]

    def web_research(self, state: WebSearchState, config: RunnableConfig) -> OverallState:
        """LangGraph节点，使用Tavily搜索API执行网络研究。"""
        search_query = state["search_query"]
        query_id = state["id"]

        stream_output("web_research", f"开始搜索：{search_query}", "start",
                      {"query_id": query_id})
        logger.info(f"🔍 执行搜索: {search_query}")

        try:
            # 使用Tavily执行搜索
            response = tavily_client.search(
                query=search_query,
                max_results=10,
                time_range="month",
                include_raw_content="markdown",
                country="china"
            )

            # 格式化搜索结果
            formatted_results = self.format_tavily_results(response)

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

            result_count = len(response.get('results', []))
            stream_output("web_research", f"找到 {result_count} 个搜索结果", "complete",
                          {"result_count": result_count, "query_id": query_id})
            logger.info(f"✅ 找到 {result_count} 个结果")

            return {
                "sources_gathered": sources,
                "search_query": [search_query],
                "web_research_result": [formatted_results],
            }

        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            stream_output("web_research", error_msg, "error", {"query_id": query_id})
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

    def reflection(self, state: OverallState, config: RunnableConfig) -> ReflectionState:
        """LangGraph节点，识别知识缺口并生成潜在的后续查询。"""
        configurable = Configuration.from_runnable_config(config)
        state["research_loop_count"] = state.get("research_loop_count", 0) + 1

        stream_output("reflection", "开始分析研究结果，识别知识缺口", "start",
                      {"loop_count": state["research_loop_count"]})

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
        response = self.conversation_model.invoke(formatted_prompt)
        content = response.content

        # 解析JSON响应
        try:
            content.replace("```json", "").replace("```", "")
            result = json.loads(content)
            is_sufficient = result.get("is_sufficient", True)
            knowledge_gap = result.get("knowledge_gap", "")
            follow_up_queries = result.get("follow_up_queries", [])

            status = "足够" if is_sufficient else "不足够"
            stream_output("reflection", f"分析完成：当前信息{status}", "complete",
                          {"is_sufficient": is_sufficient, "follow_up_count": len(follow_up_queries)})

            logger.info(f"📊 反思结果: {status}")
            if not is_sufficient:
                logger.info(f"💭 知识缺口: {knowledge_gap}")
                logger.info(f"🔄 后续查询: {follow_up_queries}")
                stream_output("reflection", f"需要进行{len(follow_up_queries)}个后续查询", "info")

            return {
                "is_sufficient": is_sufficient,
                "knowledge_gap": knowledge_gap,
                "follow_up_queries": follow_up_queries,
                "research_loop_count": state["research_loop_count"],
                "number_of_ran_queries": len(state["search_query"]),
            }
        except Exception as e:
            logger.error(f"解析反思结果失败: {e}")
            stream_output("reflection", "解析反思结果失败，默认为足够", "error")
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

    def finalize_answer(self, state: OverallState, config: RunnableConfig):
        """LangGraph节点，完成研究摘要。"""
        stream_output("finalize_answer", "开始生成最终答案\n", "start")

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

        # 流式生成最终答案
        content = ""
        for chunk in self.conversation_model.stream(formatted_prompt):
            content += chunk.content
            stream_output("finalize_answer", chunk.content, "streaming")

        logger.info("🎯 生成最终答案完成")
        stream_output("finalize_answer", "最终答案生成完成", "complete")

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

    def create_graph(self) -> StateGraph:
        """创建LangGraph"""
        builder = StateGraph(OverallState, config_schema=Configuration)

        # 定义节点
        builder.add_node("generate_query", self.generate_query)
        builder.add_node("web_research", self.web_research)
        builder.add_node("reflection", self.reflection)
        builder.add_node("finalize_answer", self.finalize_answer)

        # 设置图的边
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

    def run_with_streaming(self, messages: List[HumanMessage]) -> Iterator[Dict]:
        """使用流式输出运行智能体"""
        self.is_running = True

        # 清空队列
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break

        # 创建智能体图
        graph = self.create_graph()

        # 存储最终结果
        result_container = {}

        def run_graph():
            # 设置流式输出回调到当前上下文
            token = stream_callback.set(self._stream_callback)
            try:
                result = graph.invoke({"messages": messages})
                result_container["result"] = result
            except Exception as e:
                result_container["error"] = str(e)
                logger.error(f"图执行失败: {e}")
            finally:
                # 发送结束信号
                try:
                    self.output_queue.put_nowait({
                        "type": "end",
                        "node": "system",
                        "content": "执行完成"
                    })
                except:
                    pass
                # 重置上下文
                stream_callback.reset(token)
                self.is_running = False

        # 启动图执行线程
        thread = threading.Thread(target=run_graph)
        thread.start()

        # 从队列中yield输出
        while self.is_running or not self.output_queue.empty():
            try:
                # 等待输出，设置超时以避免无限等待
                output = self.output_queue.get(timeout=0.5)
                yield output

                # 如果收到结束信号，准备结束
                if output.get("type") == "end":
                    break

            except queue.Empty:
                # 检查线程是否还在运行
                if not thread.is_alive():
                    break
                continue

        # 等待线程完成
        thread.join(timeout=5)  # 设置超时避免无限等待

        # 返回最终结果
        if "result" in result_container:
            yield {
                "type": "final_result",
                "node": "system",
                "content": "任务完成",
                "result": result_container["result"]
            }
        elif "error" in result_container:
            yield {
                "type": "error",
                "node": "system",
                "content": f"执行出错: {result_container['error']}"
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


# 测试代码
if __name__ == "__main__":
    # 创建用户消息
    agent = StreamingGraph()

    # 可以多次调用同一个实例
    for i, query in enumerate(["搜索上海天气", "搜索深圳天气"], 1):
        print(f"\n--- 第{i}次查询: {query} ---")
        user_msg = HumanMessage(content=query)

        for output in agent.run_with_streaming([user_msg]):
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
                break
