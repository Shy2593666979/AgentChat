import copy
import time
import asyncio
from loguru import logger
from typing import List, Dict, Any
from pydantic import BaseModel
from langgraph.types import Command
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import wrap_tool_call, ToolCallLimitMiddleware
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, AIMessageChunk

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.core.callbacks import usage_metadata_callback
from agentchat.services.rag_handler import RagHandler
from agentchat.tools import WeChatTools
from agentchat.schema.usage_stats import UsageStatsAgentType
from agentchat.schema.workspace import WorkSpaceAgents
from agentchat.api.services.user import UserService
from agentchat.services.mcp.manager import MCPManager
from agentchat.prompts.chat import GenerateTitlePrompt
from agentchat.utils.convert import convert_mcp_config
from agentchat.core.models.manager import ModelManager
from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.database.models.workspace_session import WorkSpaceSessionCreate, WorkSpaceSessionContext


class MCPConfig(BaseModel):
    url: str
    type: str = "sse"
    tools: List[str] = []
    server_name: str
    mcp_server_id: str


class WeChatAgent:
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
    ``WeChatAgent`` instances are automatically created by.
    End-users rarely need to touch this class directly.
    """

    def __init__(self,
                 user_id: str,
                 session_id: str,
                 wechat_account_user: str = None,
                 plugins: List[str] = [],
                 mcp_configs: List[MCPConfig] = []):

        # WeChat-agent only needs tool calling model, not conversation model
        self.model = ModelManager.get_conversation_model()
        self.plugin_tools = []
        self.mcp_tools = []
        self.mcp_configs = mcp_configs
        self.tools = []
        self.mcp_manager = MCPManager(convert_mcp_config([mcp_config.model_dump() for mcp_config in mcp_configs]))
        self.plugins = plugins
        self.session_id = session_id
        self.wechat_account_user = wechat_account_user
        self.user_id = user_id

        # Find user config by server name
        self.server_dict: dict[str, Any] = {}

        # Initialize state management
        self._initialized = False


    async def init_wechat_agent(self):
        """Initialize sub-agent - with resource management"""
        try:
            if self._initialized:
                logger.info("WeChat Agent already initialized")
                return
            await self.setup_mcp_tools()
            await self.setup_plugin_tools()

            self.middlewares = await self.setup_middlewares()

            self.tools = self.plugin_tools + self.mcp_tools
            self._initialized = True
            self.react_agent = self.setup_react_agent()

            logger.info("WeChat Agent initialized successfully")
        except Exception as err:
            logger.error(f"Failed to initialize WeChat Agent: {err}")
            raise

    def setup_react_agent(self):
        return create_agent(
            model=self.model,
            tools=self.tools,
            middleware=self.middlewares
        )

    async def setup_middlewares(self):
        tool_call_limiter = ToolCallLimitMiddleware(
            thread_limit=1,
        )

        @wrap_tool_call
        async def handler_call_mcp_tool(
            request: ToolCallRequest,
            handler
        ) -> ToolMessage | Command:
            if self.is_mcp_tool(request.tool_call["name"]):
                # 针对鉴权的MCP Server需要用户的单独配置，例如飞书、邮箱
                mcp_config = await MCPUserConfigService.get_mcp_user_config(self.user_id, self.get_mcp_id_by_tool(request.tool_call["name"]))
                request.tool_call["args"].update(mcp_config)
                tool_result = await handler(request)
                print(tool_result)
            else:
                tool_result = await handler(request)

            return tool_result

        return [tool_call_limiter, handler_call_mcp_tool]

    async def setup_mcp_tools(self):
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

    async def setup_plugin_tools(self):
        """Initialize plugin tools - with error handling"""
        try:
            for tool_name, tool in WeChatTools.items():
                self.plugin_tools.append(tool)

            logger.info(f"Loaded {len(self.plugin_tools)} plugin tools")

        except Exception as err:
            logger.error(f"Failed to initialize plugin tools: {err}")
            self.plugin_tools = []

    async def retrival_knowledge_documents(self, query):
        wechat_account_user_id = UserService.get_user_id_by_name(self.wechat_account_user)
        knowledges = await KnowledgeService.select_knowledge(wechat_account_user_id)
        if not knowledges:
            return None
        collection_name = knowledges[0]["id"] # 时间有限，只检索一个知识库
        document = await RagHandler.retrieve_ranked_documents(
            top_k=3,
            min_score=0.01,
            query=query,
            index_names=[collection_name],
            collection_names=[collection_name],
            needs_query_rewrite=False
        )

        return document

    async def ainvoke(self, messages: List[BaseMessage]):
        """Sub-agent tool execution - only return tool execution results, no model reply"""

        if not self._initialized:
            await self.init_wechat_agent()
        user_messages = copy.deepcopy(messages)
        try:
            react_agent_task = None
            if self.tools and len(self.tools) != 0:
                react_start = time.perf_counter()
                react_agent_task = asyncio.create_task(
                    self.react_agent.ainvoke(
                        input={"messages": messages},
                        config={"callbacks": [usage_metadata_callback]}
                    )
                )

            retrival_start = time.perf_counter()
            retrival_task = asyncio.create_task(self.retrival_knowledge_documents(query=user_messages[-1].content))

            # 检索知识库补充信息
            retrival_result = await retrival_task
            retrival_elapsed = time.perf_counter() - retrival_start
            logger.info(f"Retrieval task completed in {retrival_elapsed:.2f}s")

            if retrival_result:
                user_messages[0].content = user_messages[0].content + f"\n\n ## 补充信息 \n {retrival_result}"

            # Wait for tool execution to complete
            react_agent_result = None
            if react_agent_task:
                try:
                    react_agent_result = await asyncio.wait_for(react_agent_task, timeout=1.0)
                    react_elapsed = time.perf_counter() - react_start
                    logger.info(f"React agent task completed in {react_elapsed:.2f}s")
                except asyncio.TimeoutError:
                    logger.warning("React agent task timeout after 1s, cancelling...")
                    react_agent_task.cancel()
                    try:
                        await react_agent_task
                    except asyncio.CancelledError:
                        logger.info("React agent task cancelled due to timeout")
                except Exception as e:
                    logger.error(f"React agent task failed: {e}")

            if react_agent_result:
                messages = react_agent_result["messages"][:-1]  # Remove messages that didn't hit tools
                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]

        except Exception as err:
            raise ValueError from err

        messages = user_messages + messages
        response = await self.model.ainvoke(messages)

        await self._add_workspace_session(
            title="微信公众号对话",
            contexts=WorkSpaceSessionContext(
                query=user_messages[-1].content,
                answer=response.content
            ))
        return response

    async def _generate_title(self, query):
        session = await WorkSpaceSessionService.get_workspace_session_from_id(self.session_id, self.wechat_account_user)
        if session:
            return session.get("title")
        title_prompt = GenerateTitlePrompt.format(query=query)
        response = await self.model.ainvoke(input=title_prompt, config={"callbacks": [usage_metadata_callback]})
        return response.content

    async def _add_workspace_session(self, title, contexts: WorkSpaceSessionContext):
        session = await WorkSpaceSessionService.get_workspace_session_from_id(self.session_id, self.wechat_account_user)
        if session:
            await WorkSpaceSessionService.update_workspace_session_contexts(
                session_id=self.session_id,
                session_context=contexts.model_dump()
            )
        else:
            await WorkSpaceSessionService.create_workspace_session(
                WorkSpaceSessionCreate(
                    title=title,
                    user_id=self.user_id,
                    session_id=self.session_id,
                    contexts=[contexts.model_dump()],
                    agent=WorkSpaceAgents.WeChatAgent.value
                )
            )

    async def astream(self, messages: List[BaseMessage]):
        if not self._initialized:
            await self.init_wechat_agent()
        user_messages = copy.deepcopy(messages)

        try:
            react_agent_task = None
            if self.tools and len(self.tools) != 0:
                react_agent_task = asyncio.create_task(
                    self.react_agent.ainvoke(
                        input={"messages": messages},
                        config={"callbacks": [usage_metadata_callback]}
                    )
                )

            retrival_task = asyncio.create_task(self.retrival_knowledge_documents(query=user_messages[-1].content))

            # Wait for tool execution to complete
            if react_agent_task:
                results = await react_agent_task
                messages = results["messages"][:-1]  # Remove messages that didn't hit tools

                messages = [msg for msg in messages if
                            isinstance(msg, ToolMessage) or (isinstance(msg, AIMessage) and msg.tool_calls)]

            # 检索知识库补充信息
            retrival_result = await retrival_task
            if retrival_result:
                user_messages[0].content = user_messages[0].content.format(retrival_result=retrival_result)
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

        await self._add_workspace_session(
            title="微信公众号对话",
            contexts=WorkSpaceSessionContext(
                query=user_messages[-1].content,
                answer=final_answer
            ))


    async def _record_agent_token_usage(self, response: AIMessage | AIMessageChunk | BaseMessage, model):
        if response.usage_metadata:
            await UsageStatsService.create_usage_stats(
                model=model,
                user_id=self.user_id,
                agent=UsageStatsAgentType.wechat_agent,
                input_tokens=response.usage_metadata.get("input_tokens"),
                output_tokens=response.usage_metadata.get("output_tokens")
            )

    def is_mcp_tool(self, tool_name: str):
        """Determine if it's an MCP tool and return the corresponding tool instance"""
        mcp_names = [tool.name for tool in self.mcp_tools]
        plugin_names = [tool.name for tool in self.plugin_tools]

        if tool_name in mcp_names:
            return True
        elif tool_name in plugin_names:
            return False
        else:
            raise ValueError(f"Tool '{tool_name}' not found in either MCP or plugin tools.")

    def get_mcp_id_by_tool(self, tool_name):
        for server_name, tools in self.server_dict.items():
            if tool_name in tools:
                for config in self.mcp_configs:
                    if server_name == config.server_name:
                        return config.mcp_server_id
        return None
