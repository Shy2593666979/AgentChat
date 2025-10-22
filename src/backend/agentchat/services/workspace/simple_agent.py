import asyncio
import copy

from loguru import logger
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, Tool, StructuredTool
from langgraph.graph import MessagesState, StateGraph, END, START

from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.database.models.workspace_session import WorkSpaceSessionCreate, WorkSpaceSessionContext
from agentchat.schema.workspace import WorkSpaceAgents
from agentchat.tools import WorkSpacePlugins
from agentchat.api.services.tool import ToolService
from agentchat.services.mcp.manager import MCPManager
from agentchat.schema.mcp import MCPBaseConfig
from agentchat.prompts.chat import DEFAULT_CALL_PROMPT, GenerateTitlePrompt
from agentchat.utils.convert import mcp_tool_to_args_schema, function_to_args_schema
from agentchat.core.models.manager import ModelManager

class WorkSpaceSimpleAgent:
    """

    Sub-agent that can invoke **both user-provided plugin functions and MCP tools**.  It analyses the
    current conversation, decides which tool(s) should be run, performs the calls asynchronously and
    pushes progress/result events back to the main :class:`mars_agent.agent.MarsAgent`.

    Responsibilities
    ---------------
    1. Select appropriate plugin or MCP tool according to conversation context.
    2. Execute the tool in an asynchronous, non-blocking way.
    3. Report every progress, success or error through the shared ``EventManager``.
    4. **Does not generate any LLM response** – that task belongs to the main agent.

    Usage
    -----
    ``SimpleAgent`` instances are automatically created by.
    End-users rarely need to touch this class directly.
    """

    def __init__(self,
                 model_config,
                 user_id: str,
                 mcp_configs: List[MCPBaseConfig] = [],
                 plugins: List[str] = []):

        # Sub-agent only needs tool calling model, not conversation model
        self.model = ModelManager.get_user_model(**model_config)
        self.plugin_tools = []
        self.mcp_tools = []
        self.graph = None
        self.mcp_configs = mcp_configs
        self.tools = []
        self.mcp_manager = MCPManager(mcp_configs)
        self.plugins = plugins

        self.step_counter_lock = asyncio.Lock()
        self.step_counter = 1

        self.user_id = user_id
        # Record tool call count
        self.tool_call_count: dict[str, int] = {}

        # Find user config by server name
        self.server_dict: dict[str, Any] = {}

        # Initialize state management
        self._initialized = False


    async def init_simple_agent(self):
        """Initialize sub-agent - with resource management"""
        try:
            if self._initialized:
                logger.info("Simple Agent already initialized")
                return

            await self.set_agent_graph()
            await self.init_mcp_tools()
            await self.init_plugin_tools()

            self.tools = self.plugin_tools + self.mcp_tools
            self._initialized = True
            logger.info("Simple Agent initialized successfully")

        except Exception as err:
            logger.error(f"Failed to initialize Simple Agent: {err}")
            raise

    async def init_mcp_tools(self):
        """Initialize MCP tools - with error handling"""
        if not self.mcp_configs:
            self.mcp_tools = []
            return

        try:
            # Establish connection with MCP Server
            self.mcp_tools = await self.mcp_manager.get_mcp_tools()

            mcp_servers_info = await self.mcp_manager.show_mcp_tools()
            self.server_dict = {server_name: [tool["name"] for tool in tools_info] for server_name, tools_info in
                                mcp_servers_info.items()}

            logger.info(f"Loaded {len(self.mcp_tools)} MCP tools from MCP servers")

        except Exception as err:
            logger.error(f"Failed to initialize MCP tools: {err}")
            self.mcp_tools = []

    async def init_plugin_tools(self):
        """Initialize plugin tools - with error handling"""
        try:
            tools_name = await ToolService.get_tool_name_by_id(self.plugins)
            for name in tools_name:
                self.plugin_tools.append(StructuredTool(name=name, description=WorkSpacePlugins[name].__doc__, func=WorkSpacePlugins[name]))

            logger.info(f"Loaded {len(self.plugin_tools)} plugin tools")

        except Exception as err:
            logger.error(f"Failed to initialize plugin tools: {err}")
            self.plugin_tools = []

    async def call_tools_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """Tool selection - sub-agent responsible for tool calling decision"""

        call_tool_messages: List[BaseMessage] = []
        # Only initialize when calling tools for the first time
        if self.step_counter == 1:
            tools_schema = []
            for tool in self.tools:
                if isinstance(tool, BaseTool) and tool.args_schema:  # MCP Tool
                    tools_schema.append(mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema))
                else:
                    tools_schema.append(function_to_args_schema(tool.func))

            self.tool_invocation_model = self.model.bind_tools(tools_schema)

        system_message = SystemMessage(content=DEFAULT_CALL_PROMPT)
        call_tool_messages.append(system_message)
        call_tool_messages.extend(messages)

        response = await self.tool_invocation_model.ainvoke(call_tool_messages)
        # Determine if there are tools available for calling
        if response.tool_calls:
            return response
        else:
            return AIMessage(content="No available tools found")

    async def execute_tool_message(self, messages: List[ToolMessage]):
        """Tool execution - sub-agent responsible for specific tool execution"""
        tool_calls = messages[-1].tool_calls
        tool_messages: List[BaseMessage] = []

        # Ensure no race conditions occur
        async with self.step_counter_lock:
            self.step_counter += 1

        for tool_call in tool_calls:

            is_mcp_tool, use_tool = self.find_tool_use(tool_call["name"])
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            if is_mcp_tool:
                try:
                    personal_config = self.get_mcp_config_by_tool(tool_name)
                    if personal_config:
                        tool_args.update(personal_config)

                    # Call MCP tool to return all results, but currently only handle text data
                    text_content, no_text_content = await use_tool.coroutine(**tool_args)

                    tool_messages.append(
                        ToolMessage(content=text_content, name=tool_name, tool_call_id=tool_call_id))
                    logger.info(f"MCP Tool {tool_name}, Args: {tool_args}, Result: {text_content}")

                except Exception as err:
                    logger.error(f"MCP Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))
            else:

                try:
                    # Add suffix to ensure event messages don't get stuck
                    suffix = " " * self.tool_call_count.get(tool_name, 0)
                    self.tool_call_count[tool_name] = self.tool_call_count.get(tool_name, 0) + 1

                    if hasattr(use_tool, "coroutine") and use_tool.coroutine is not None:
                        tool_result = await use_tool.coroutine(**tool_args)
                    else:
                        # Convert to async
                        tool_result = await asyncio.to_thread(use_tool.func, **tool_args)

                    tool_messages.append(
                        ToolMessage(content=tool_result, name=tool_name, tool_call_id=tool_call_id))
                    logger.info(f"Plugin Tool {tool_name}, Args: {tool_args}, Result: {tool_result}")

                except Exception as err:
                    logger.error(f"Plugin Tool {tool_name} Error: {str(err)}")
                    tool_messages.append(
                        ToolMessage(content=str(err), name=tool_name, tool_call_id=tool_call_id))

        return tool_messages

    async def set_agent_graph(self):
        """Set up sub-agent's tool execution graph"""

        # Build tool calling Graph
        async def should_continue(state: MessagesState):
            messages = state["messages"]
            last_message = messages[-1]

            # If tool recursive calls exceed 5 times, return END directly
            if self.step_counter > 5:
                return END

            if last_message.tool_calls:
                return "execute_tool_node"
            else:
                return END

        async def call_tool_node(state: MessagesState):
            messages = state["messages"]

            tool_message = await self.call_tools_messages(messages)
            messages.append(tool_message)

            return {"messages": messages}

        async def execute_tool_node(state: MessagesState):
            messages = state["messages"]

            tool_results = await self.execute_tool_message(messages)
            messages.extend(tool_results)

            return {"messages": messages}

        workflow = StateGraph(MessagesState)

        workflow.add_node("call_tool_node", call_tool_node)
        workflow.add_node("execute_tool_node", execute_tool_node)

        # Set start node
        workflow.add_edge(START, "call_tool_node")
        # Set edge to determine whether to call tools
        workflow.add_conditional_edges("call_tool_node", should_continue)
        # Detect if tool recursion information exists
        workflow.add_edge("execute_tool_node", "call_tool_node")

        self.graph = workflow.compile()

    async def ainvoke(self, messages: List[BaseMessage]):
        """Sub-agent tool execution - only return tool execution results, no model reply"""
        if not self._initialized:
            await self.init_simple_agent()

        try:
            graph_task = None
            if self.tools and len(self.tools) != 0:
                graph_task = asyncio.create_task(self.graph.ainvoke({"messages": messages}))

            # Wait for tool execution to complete
            if graph_task:
                results = await graph_task
                messages = results["messages"][:-1]  # Remove messages that didn't hit tools

                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]

                return messages
            else:
                return []

        except Exception as err:
            return []

    async def _generate_title(self, query):
        title_prompt = GenerateTitlePrompt.format(query=query)
        response = await self.model.ainvoke(title_prompt)
        return response.content

    async def _add_workspace_session(self, title, contexts: WorkSpaceSessionContext):
        await WorkSpaceSessionService.create_workspace_session(
            WorkSpaceSessionCreate(
                title=title,
                user_id=self.user_id,
                contexts=[contexts.model_dump()],
                agent=WorkSpaceAgents.SimpleAgent.value))

    async def astream(self, messages: List[BaseMessage]):
        if not self._initialized:
            await self.init_simple_agent()
        user_messages = copy.deepcopy(messages)

        generate_title_task = asyncio.create_task(self._generate_title(user_messages[0].content))
        try:
            graph_task = None
            if self.tools and len(self.tools) != 0:
                graph_task = asyncio.create_task(self.graph.ainvoke({"messages": messages}))

            # Wait for tool execution to complete
            if graph_task:
                results = await graph_task
                messages = results["messages"][:-1]  # Remove messages that didn't hit tools

                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]
        except Exception as err:
            raise ValueError from err
        messages = user_messages + messages

        final_answer = ""
        async for chunk in self.model.astream(messages):
            yield {
                "event": "task_result",
                "data":{
                    "message": chunk.content
                }
            }
            final_answer += chunk.content

        await generate_title_task
        title = generate_title_task.result() if generate_title_task.done() else None

        await self._add_workspace_session(
            title=title,
            contexts=WorkSpaceSessionContext(
                query=user_messages[0].content,
                answer=final_answer
            ))



    # Additional helper methods
    def find_tool_use(self, tool_name: str):
        """Determine if it's an MCP tool and return the corresponding tool instance"""
        for tool in self.mcp_tools:
            if tool.name == tool_name:
                return True, tool

        for tool in self.plugin_tools:
            if tool.name == tool_name:
                return False, tool

        raise ValueError(f"Tool does not exist in the system: {tool_name}")

    # Get MCP Server's user config
    def get_mcp_config_by_tool(self, tool_name):
        for server_name, tools in self.server_dict.items():
            if tool_name in tools:
                for config in self.mcp_configs:
                    if server_name == config.server_name:
                        return config.personal_config or {}
        return {}
