import asyncio
import copy
from typing import List
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, Tool
from langgraph.graph import MessagesState, StateGraph, END, START
from pydantic.v1 import BaseModel

from agentchat.core.models.manager import ModelManager
from agentchat.api.services.tool import ToolService
from agentchat.services.rag_handler import RagHandler
from agentchat.tools import Call_Tool
from agentchat.api.services.llm import LLMService
from agentchat.services.mcp.manager import MCPManager
from agentchat.api.services.mcp_stdio_server import MCPServerService
from loguru import logger
import inspect
import json

INCLUDE_MSG = {"content", "id"}

FUNCTION_CALL_MSG = "Function Call"
REACT_MSG = "React"

DEFAULT_CALL_PROMPT = """
你是一个智能助手，能够根据用户的需求调用适当的工具来完成任务。以下是你的工作流程：
    1.分析用户输入：仔细阅读用户的当前查询和对话历史，理解用户的意图。
    2.判断是否需要调用工具：如果用户的请求需要特定工具的支持（例如搜索、计算、翻译等），请明确指出需要调用哪个工具。
    3.生成调用指令：如果需要调用工具，请按照以下格式生成调用指令：
        - 工具名称：工具的具体名称。
        - 输入参数：根据工具要求，从当前查询或对话历史中提取必要的信息作为输入参数。
    4.返回结果或下一步行动：如果没有工具需要调用，直接回答用户的问题或提供相关信息。
"""

class AgentConfig(BaseModel):
    mcp_ids: List[str]
    knowledge_ids: List[str]
    tool_ids: List[str]
    system_prompt: str
    use_embedding: bool = False
    llm_id: str

class ChatAgent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.mcp_manager = MCPManager(timeout=10)


    async def init_agent(self):
        self.tools = await self.set_tools()
        self.mcp_tools = await self.set_mcp_tools()
        self.tools.extend(self.mcp_tools)

        self.collection_names, self.index_names = await self.set_knowledge_names()
        await self.set_language_model()
        await self.set_agent_graph()

    async def set_language_model(self):
        self.conversation_model = ModelManager.get_conversation_model()
        self.tool_invocation_model = ModelManager.get_tool_invocation_model()
        self.reasoning_model = ModelManager.get_reasoning_model()

    async def set_mcp_tools(self) -> List[BaseTool]:
        mcp_tools = await self.mcp_manager.get_mcp_tools()
        return mcp_tools

    async def set_tools(self) -> List[BaseTool]:
        tools = []
        tools_name = await ToolService.get_tool_name_by_id(self.agent_config.tool_ids)
        for name in tools_name:
            tools.append(Tool(name=name, description=Call_Tool[name].__doc__, func=Call_Tool[name]))
        return tools

    async def set_knowledge_names(self):
        return self.agent_config.knowledge_ids, self.agent_config.knowledge_ids

    async def call_tools_messages(self, messages: List[BaseMessage]) -> BaseMessage:
        for tool in self.tools:
            if isinstance(tool, BaseTool) and tool.args_schema:
                tool.args_schema = function_to_args_schema(tool.func)

        self.tool_invocation_model.bind_tools(self.tools)

        system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
        call_tool_messages = [system_message, messages[-1]]

        response = await self.tool_invocation_model.ainvoke(call_tool_messages)
        if response.additional_kwargs:
            return AIMessage(
                content="",
                additional_kwargs=response.additional_kwargs,
                usage_metadata=response.usage_metadata,
                tool_calls=response.tool_calls,
                id=response.id,
                response_metadata=response.response_metadata
            )
        else:
            return AIMessage(content="没有命中可用的工具")

    async def execute_tool_message(self, messages: List[BaseMessage]):
        tool_calls = messages[-1].tool_calls
        tool_messages: List[BaseMessage] = []
        for tool_call in tool_calls:
            is_mcp_tool, use_tool = self.mcp_tool_use(tool_call["name"])
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            if is_mcp_tool:
                try:
                    tool_result = await use_tool.coroutine(tool_name, tool_args)
                    tool_messages.append(
                        ToolMessage(content=tool_result, name=tool_name + "_mcp", tool_call_id=tool_call_id))
                    logger.info(f"MCP Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")
                except Exception as err:
                    logger.error(f"MCP Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name + "_mcp", tool_call_id=tool_call_id))
            else:
                try:
                    tool_result = use_tool.func(tool_args)
                    tool_messages.append(
                        ToolMessage(content=tool_result, name=tool_name, tool_call_id=tool_call_id))
                    logger.info(f"Plugin Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")
                except Exception as err:
                    logger.error(f"Plugin Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))
        return tool_messages


    async def call_knowledge_messages(self, messages: List[BaseMessage]) -> BaseMessage:
        knowledge_query = messages[-1].content

        # Milvus和ES检索相关的知识库
        knowledge_message = await RagHandler.retrieve_ranked_documents(knowledge_query, self.collection_names, self.index_names)
        return SystemMessage(content=knowledge_message)


    async def ainvoke(self, messages: List[BaseMessage]):
        knowledge_message = await self.call_knowledge_messages(copy.deepcopy(messages))

        await self.graph.ainvoke({"messages": messages})
        messages.append(knowledge_message)

        async for chunk in self.conversation_model.astream(messages):
            yield chunk.content

    async def set_agent_graph(self):

        # 构建调用工具Graph
        async def should_continue(state: MessagesState):
            messages = state["messages"]
            last_message = messages[-1]

            if last_message.tool_calls:
                return "execute_tool_node"
            else:
                return END

        async def call_tool_node(state: MessagesState):
            messages = state["messages"]
            tool_message = await self.call_tools_messages(messages)
            messages.extend(tool_message)

            return {"messages": messages}

        async def execute_tool_node(state: MessagesState):
            messages = state["messages"]
            tool_results = await self.execute_tool_message(messages)
            messages.extend(tool_results)

            return {"messages": messages}

        workflow = StateGraph(MessagesState)

        workflow.add_node("call_tool_node", call_tool_node)
        workflow.add_node("execute_tool_node", execute_tool_node)

        # 设置起始节点
        workflow.add_edge(START, "call_tool_node")
        # 设置判断是否调用工具边
        workflow.add_conditional_edges("call_tool_node", should_continue)
        # 检测是否存在工具递归信息
        workflow.add_edge("execute_tool_node", "call_tool_node")

        self.graph = workflow.compile()


    async def connect_mcp_server(self):
        servers = []
        for mcp_id in self.agent_config.mcp_ids:
            server = MCPServerService.get_mcp_server_user(mcp_id)
            servers.append(server)

        await self.mcp_manager.connect_mcp_servers(servers)

    def mcp_tool_use(self, tool_name):
        for tool in self.tools:
            if tool.name == tool_name and tool in self.mcp_tools:
                return True, tool
            elif tool.name == tool_name:
                return False, tool
        return False, None


def function_to_args_schema(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown schema annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"schema": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "schema": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "schema": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }

# class ChatService:
#     def __init__(self, **kwargs):
#         self.llm_id = kwargs.get('llm_id')
#         self.tools_id = kwargs.get('tool_id')
#         self.dialog_id = kwargs.get('dialog_id')
#         self.mcp_ids = kwargs.get("mcp_ids")
#         self.embedding_id = kwargs.get('embedding_id')
#         self.knowledges_id = kwargs.get('knowledge_id')
#         self.mcp_manager = MCPManager(timeout=10)
#         self.llm_call = None
#         self.mcp_tools = None
#         self.llm = None
#         self.embedding = None
#         self.tools = []
#
#
#     async def init_agent(self):
#         await self.init_mcp()
#         await self.setup_llm()
#         await self.setup_tools()
#         await self.setup_mcp_tools()
#
#     async def setup_llm(self):
#         llm_config = LLMService.get_llm_by_id(llm_id=self.llm_id)
#         self.llm = ChatOpenAI(model=llm_config.model,
#                               base_url=llm_config.base_url, api_key=llm_config.api_key)
#
#         self.llm_call = FUNCTION_CALL_MSG if llm_config.model in Function_Call_provider else REACT_MSG
#         # Agent支持Embedding后初始化
#         if self.embedding_id:
#             await self.init_embedding()
#
#     async def init_embedding(self):
#
#         embedding_config = LLMService.get_llm_by_id(llm_id=self.embedding_id)
#         self.embedding = OpenAIEmbeddings(model=embedding_config.model,
#                                           base_url=embedding_config.base_url, api_key=embedding_config.api_key)
#
#     async def init_mcp(self):
#         servers = []
#         for mcp_id in self.mcp_ids:
#             server = MCPServerService.get_mcp_server_user(mcp_id)
#             servers.append(server)
#
#         await self.mcp_manager.connect_mcp_servers(servers)
#
#     async def setup_mcp_tools(self):
#         mcp_tools = await self.mcp_manager.get_mcp_tools()
#         self.mcp_tools = mcp_tools
#
#     async def setup_tools(self):
#         tools_name = ToolService.get_tool_name_by_id(self.tools_id)
#         if self.llm_call == REACT_MSG:
#             for name in tools_name:
#                 func = action_React[name]
#                 self.tools.append(ChatService.function_to_json(func))
#         else:
#              for name in tools_name:
#                 self.tools.append(action_Function_call[name])
#
#
#     async def run(self, messages: List[BaseMessage]):
#
#         user_input = messages[-1].content
#         # 都是通过检索RAG，并发可以减少消耗时间
#         history_messages, recall_knowledge_data = await asyncio.gather(
#             self.get_history_message(user_input=user_input, dialog_id=self.dialog_id),
#             RagHandler.rag_query(user_input, self.knowledges_id)
#         )
#
#         messages.extend(history_messages)
#         # history_message = await self.get_history_message(user_input=user_input, dialog_id=self.dialog_id)
#         # recall_knowledge_data = await RagHandler.rag_query(user_input, self.knowledges_id)
#
#         if self.llm_call == 'React':
#             return self._run_react(messages, recall_knowledge_data)
#         else:
#             return self._run_function_call(messages, recall_knowledge_data)
#
#     async def _run_react(self, messages: List[BaseMessage], recall_knowledge_data: str):
#         agent = create_structured_chat_agent(llm=self.llm, tools=self.tools)
#         agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
#         messages.append(AIMessage(content=recall_knowledge_data))
#
#         async for chunk in agent_executor.astream(messages):
#             yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
#
#     async def _run_function_call(self, user_input: str, history_message: str, recall_knowledge_text: str):
#
#         # 并发执行不同类型的工具
#         tools_result, mcp_tools_result = asyncio.gather(
#             self.call_common_tool(user_input, history_message),
#             self.call_mcp_tool(user_input, history_message)
#         )
#
#
#         prompt_template = PromptTemplate.from_template(function_call_prompt)
#
#         chain = prompt_template | self.llm
#         async for chunk in chain.astream({'input': user_input, 'history': history_message, 'tools_result': tools_result, "mcp_tools_result": mcp_tools_result, "knowledge_result": recall_knowledge_text}):
#             yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
#
#     async def call_common_tool(self, user_input, history_message):
#         # 普通的插件调用
#         func_prompt = function_call_template.format(input=user_input, history=history_message)
#         fun_name, args = await self._function_call(user_input=func_prompt)
#         tools_result = self.exec_tools(fun_name, args)
#         return tools_result
#
#     async def call_mcp_tool(self, user_input, history_message):
#         # MCP 插件调用
#         mcp_tool_prompt = function_call_template.format(input=user_input, history=history_message)
#         mcp_tool_name, mcp_tool_args = await self._mcp_function_call(user_input=mcp_tool_prompt)
#         mcp_tool_result = self.exec_mcp_tools(mcp_tool_name, mcp_tool_args)
#         return mcp_tool_result
#
#     async def _function_call(self, user_input: str):
#         messages = [HumanMessage(content=user_input)]
#         message = self.llm.invoke(
#             messages,
#             functions=self.tools,
#         )
#         try:
#             if message.additional_kwargs:
#                 function_name = message.additional_kwargs["function_call"]["name"]
#                 arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])
#
#                 logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
#                 return function_name, arguments
#             else:
#                 raise ValueError
#         except Exception as err:
#             logger.info(f"Function call is not appear: {err}")
#             return None, None
#
#     async def _mcp_function_call(self, user_input: str):
#         messages = [HumanMessage(content=user_input)]
#         message = self.llm.invoke(
#             messages,
#             functions=self.mcp_tools,
#         )
#         try:
#             if message.additional_kwargs:
#                 function_name = message.additional_kwargs["function_call"]["name"]
#                 arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])
#
#                 logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
#                 return function_name, arguments
#             else:
#                 raise ValueError
#         except Exception as err:
#             logger.info(f"Function call is not appear: {err}")
#             return None, None
#
#     async def exec_mcp_tools(self, mcp_tool_name, mcp_tool_args):
#         mcp_tools_info = {
#             "tool_name": mcp_tool_name,
#             "tool_args": mcp_tool_args
#         }
#         mcp_tool_results = self.mcp_manager.call_mcp_tools([mcp_tools_info])
#         return mcp_tool_results
#
#     async def exec_tools(self, func_name, args):
#         try:
#             action = action_Function_call[func_name]
#             result = action(**args)
#             return result
#         except Exception as err:
#             logger.error(f"action appear error: {err}")
#             return fail_action_prompt
#
#
#     async def get_history_message(self, user_input: str, dialog_id: str, top_k: int = 5) -> List[BaseMessage]:
#         # 如果绑定了Embedding模型，默认走RAG检索聊天记录
#         if self.embedding:
#             messages = await self._retrieval_history(user_input, dialog_id, top_k)
#             return messages
#         else:
#             messages = await self._direct_history(dialog_id, top_k)
#             return messages
#
#     @staticmethod
#     async def _direct_history(dialog_id: str, top_k: int):
#         messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k)
#         results = []
#         # for message in enumerate(messages):
#         #     if idx % 2 == 0:
#         #         results.append(HumanMessage(content=message.content))
#         #     else:
#         #         results.append(AIMessage(content=message.content))
#         return results
#
#     # 使用RAG检索的方式将最近2 * top_k条数据按照相关性排序，取其中top_k个
#     async def _retrieval_history(self, user_input: str, dialog_id: str, top_k: int):
#
#         # messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k * 2)
#         #
#         # for msg in messages:
#         #     self.collection.add(documents=[msg.to_str()], ids=[uuid4().hex])
#         #
#         # results = self.collection.query(query_texts=[user_input], n_results=top_k)
#         # history = ''.join(results['documents'][0])
#         # return history
#         messages = await RagHandler.rag_query(user_input, dialog_id, 0.6, top_k, False)
#         return [SystemMessage(content=messages)]
#
#     #@staticmethod
#
