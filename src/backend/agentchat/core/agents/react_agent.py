import time
from loguru import logger
from typing import List, Dict, Any, AsyncGenerator, NotRequired, TypedDict, Union, Optional
from langchain_core.language_models import BaseChatModel
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.config import get_stream_writer
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessageChunk, AIMessage, HumanMessage

from agentchat.core.callbacks import usage_metadata_callback
from agentchat.prompts.chat import DEFAULT_CALL_PROMPT


# 定义流式事件的负载结构，增强类型安全性
class StreamEventData(TypedDict, total=False):
    """用于 LangGraph 'custom' stream_mode 的事件数据结构"""
    title: str
    status: str  # e.g., "START", "END", "ERROR"
    message: str


# 定义流式输出的完整结构
class StreamOutput(TypedDict):
    type: str  # e.g., "event", "response_chunk"
    timestamp: float
    data: Union[StreamEventData, Dict[str, str]]


# 优化的状态类型
class ReactAgentState(MessagesState):
    """LangGraph 状态，继承自 MessagesState"""
    tool_call_count: NotRequired[int]
    model_call_count: NotRequired[int]


# --- 核心 ReactAgent 类 ---

class ReactAgent:
    """
    一个基于 LangGraph 的 ReAct (Reasoning and Acting) 代理。
    它支持流式输出，并在工具调用和模型推理过程中发送自定义事件。
    """

    def __init__(self,
                 model: BaseChatModel,
                 system_prompt: Optional[str] = None,
                 tools: List[BaseTool] = []):

        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        self.mcp_agent_as_tools: List[BaseTool] = []  # 用于集成其他代理作为工具

        # LangGraph 实例
        self.graph: Optional[StateGraph] = None

    def _wrap_stream_output(self, type: str, data: Dict[str, Any]) -> StreamOutput:
        """
        统一的流式输出包装器。
        """
        return {
            "type": type,
            "timestamp": time.time(),
            "data": data
        }

    async def _init_agent(self):
        """延迟初始化 LangGraph，确保在首次调用 astream 时设置好。"""
        if self.graph is None:
            self.graph = await self._setup_react_graph()

    def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """根据名称获取工具实例。"""
        for tool in self.tools + self.mcp_agent_as_tools:
            if tool.name == tool_name:
                return tool
        return None

    # --- LangGraph Node 定义和 Graph Setup ---

    async def _setup_react_graph(self):
        """设置 Agent 图，定义节点和边。"""

        workflow = StateGraph(ReactAgentState)

        # 节点定义
        workflow.add_node("call_tool_node", self._call_tool_node)
        workflow.add_node("execute_tool_node", self._execute_tool_node)

        # 边和条件边
        workflow.add_edge(START, "call_tool_node")
        workflow.add_conditional_edges("call_tool_node", self._should_continue)
        workflow.add_edge("execute_tool_node", "call_tool_node")  # 工具结果 -> 模型再次推理

        return workflow.compile()

    # --- LangGraph Node Functions ---

    async def _should_continue(self, state: ReactAgentState) -> Union[str, Any]:
        """条件边：判断是否需要执行工具。"""
        last_message = state["messages"][-1]

        # 优化：如果模型回复了 content *并且* 没有 tool_calls，也应视为结束。
        if last_message.tool_calls:
            return "execute_tool_node"

        return END

    async def _call_tool_node(self, state: ReactAgentState) -> Dict[str, List[BaseMessage]]:
        """调用模型，判断是否需要工具，并发送工具选择事件。"""
        stream_writer = get_stream_writer()
        is_first_call = state.get("tool_call_count", 0) == 0

        # 优化：状态信息和事件消息使用 f-string
        select_tool_message = (
            "开始分析和选择可用工具" if is_first_call else
            f"继续分析是否需要工具（已调用 {state['tool_call_count']} 次）"
        )

        # 发送工具分析开始事件
        stream_writer(self._wrap_stream_output("event", {
            "title": select_tool_message,
            "status": "START",
            "message": "正在分析需要使用的工具...",
        }))

        tool_invocation_model = self.model.bind_tools(self.tools)
        response: AIMessage = await tool_invocation_model.ainvoke(state["messages"])

        # 判断是否有工具可调用
        if response.tool_calls:
            tool_call_names = sorted(list(set(tool_call["name"] for tool_call in response.tool_calls)))
            # 发送工具选择完成事件
            stream_writer(self._wrap_stream_output("event", {
                "title": select_tool_message,
                "status": "END",
                "message": f"命中可用工具：{', '.join(tool_call_names)}"
            }))

            state["messages"].append(response)
            return {"messages": state["messages"]}
        else:
            # 发送无工具可用事件
            stream_writer(self._wrap_stream_output("event", {
                "title": select_tool_message,
                "status": "END",
                "message": "模型选择直接回复，没有命中可用的工具"
            }))

            # 将模型的最终回复添加到消息中，LangGraph 将通过 END 结束
            state["messages"].append(response)
            return {"messages": state["messages"]}

    async def _execute_tool_node(self, state: ReactAgentState) -> Dict[str, Any]:
        """执行工具，并将结果返回给模型。"""
        stream_writer = get_stream_writer()
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        tool_messages: List[BaseMessage] = []

        if not tool_calls:
            logger.warning("Execute tool node reached without tool calls.")
            return {"messages": state["messages"], "tool_call_count": state["tool_call_count"]}

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            tool_title = f"执行工具: {tool_name}"

            try:
                # 发送工具执行开始事件
                stream_writer(self._wrap_stream_output("event", {
                    "status": "START",
                    "title": tool_title,
                    "message": f"参数: {tool_args}"
                }))

                current_tool = self.get_tool_by_name(tool_name)

                if current_tool is None:
                    tool_result = f"Error: Tool '{tool_name}' not found."
                    raise ValueError(tool_result)

                # 优化：使用 BaseTool 的 ainvoke/invoke 方法
                if current_tool.coroutine:
                    tool_result = await current_tool.ainvoke(tool_args)
                else:
                    tool_result = current_tool.invoke(tool_args)

                # 确保结果是字符串，或可转换为字符串
                tool_result_str = str(tool_result)

                # 发送插件工具执行完成事件
                stream_writer(self._wrap_stream_output("event", {
                    "status": "END",
                    "title": tool_title,
                    "message": f"结果: {tool_result_str}"
                }))

                tool_messages.append(
                    ToolMessage(content=tool_result_str, name=tool_name, tool_call_id=tool_call_id)
                )
                logger.info(f"Tool {tool_name} executed. Args: {tool_args}, Result: {tool_result_str}")

            except Exception as err:
                error_message = f"执行工具 {tool_name} 失败: {str(err)}"
                # 发送插件工具执行错误事件
                stream_writer(self._wrap_stream_output("event", {
                    "status": "ERROR",
                    "title": tool_title,
                    "message": error_message
                }))

                logger.error(f"Execute Tool {tool_name} Error: {str(err)}")
                tool_messages.append(
                    ToolMessage(content=error_message, name=tool_name, tool_call_id=tool_call_id)
                )

        state["messages"].extend(tool_messages)
        # 优化：确保 tool_call_count 是整数
        new_tool_count = state.get("tool_call_count", 0) + 1

        return {"messages": state["messages"], "tool_call_count": new_tool_count}

    # --- 主调用方法 ---

    async def astream(self, messages: List[BaseMessage]) -> AsyncGenerator[StreamOutput, None]:
        """流式调用主方法。"""

        # 消息预处理 (System Prompt)
        if not messages or not isinstance(messages[-1], (HumanMessage, AIMessage, ToolMessage)):
            # 确保最后一条消息是可交互的消息类型
            logger.warning("Input messages list is empty or last message type is unexpected.")
            return

        if self.system_prompt and not any(isinstance(m, SystemMessage) for m in messages):
            # 优化：如果用户没有提供 SystemMessage，则在最前面插入。
            system_prompt_msg = self.system_prompt if self.system_prompt else DEFAULT_CALL_PROMPT
            messages.insert(0, SystemMessage(system_prompt_msg))

        # 初始化 Graph
        await self._init_agent()

        response_content = ""
        initial_state = {"messages": messages, "tool_call_count": 0, "model_call_count": 0}

        try:
            # 使用 'values' 模式接收整个状态，'custom' 模式接收 stream_writer 事件
            async for typ, token in self.graph.astream(
                    input=initial_state,
                    config={"callbacks": [usage_metadata_callback]},
                    stream_mode=["messages", "custom"],
            ):
                # 处理自定义事件
                if typ == "custom":  # LangGraph 的 custom 模式直接返回事件内容
                    yield self._wrap_stream_output("event", token)
                # 处理 AIMessageChunk (模型内容流)
                if typ == "messages" and isinstance(token[0], AIMessageChunk):
                    response_content += token[0].content
                    yield self._wrap_stream_output("response_chunk", {
                        "chunk": token[0].content,
                        "accumulated": response_content
                    })

        # 兜底错误处理
        except Exception as err:
            logger.error(f"Agent Execution Error: {err}")

            # 如果是空回复，则发送错误信息
            if not response_content:
                error_chunk = "您的问题可能触发了模型的限制，或执行过程中发生错误。请尝试换个问法。"
                yield self._wrap_stream_output("response_chunk", {
                    "chunk": error_chunk,
                    "accumulated": response_content + error_chunk
                })
