import asyncio
import json
from typing import List
from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.chat import FIX_JSON_PROMPT, PLAN_CALL_TOOL_PROMPT, SINGLE_PLAN_CALL_PROMPT
from agentchat.schema.chat import PlanToolFlow
from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.services.mcp.manager import MCPManager
from agentchat.utils.convert import convert_mcp_config

# A Plan-and-Execute Agent Execution Paradigm
class PlanExecuteAgent:
    """
    A planning-based conversational AI agent that can execute tools and functions through strategic planning.

    The PlanExecuteAgent is designed to analyze user queries, create execution plans, and orchestrate
    tool calls to provide comprehensive responses. It supports both plugin functions and MCP (Model Context Protocol)
    tools, with real-time event streaming and error handling capabilities.

    Key Features:
        - Strategic planning before tool execution
        - Support for both sync and async functions
        - MCP (Model Context Protocol) tool integration
        - Real-time event streaming
        - Automatic JSON repair for malformed responses
        - Comprehensive error handling and logging

    Attributes:
        user_id (str): User identifier for personalization and configuration
        tools (List[BaseTool]): List of available tools for the agent
        mcp_ids (List[str]): List of MCP server IDs to be integrated
        mcp_manager (MCPManager): Manager for MCP tools and configurations
        mcp_tools (List[BaseTool]): Dynamically loaded MCP tools
        conversation_model: Model for general conversation
        tool_call_model: Model specifically for tool invocation

    Example:
        Basic usage with tools:

        ```python
        from langchain_core.tools import tool

        @tool
        def get_weather(city: str) -> str:
            '''Get current weather for a city'''
            return f"Weather in {city}: 22°C, sunny"

        agent = PlanExecuteAgent(
            user_id="user_123",
            tools=[get_weather],
            mcp_ids=["mcp_server_1"]
        )

        messages = [HumanMessage(content="What's the weather like in Tokyo?")]
        response = await agent.ainvoke(messages)
        print(response)
        ```

    Note:
        - Tools should include proper descriptions for effective planning
        - MCP servers must be properly configured and accessible
        - The agent automatically handles JSON parsing errors with repair attempts
        - Planning phase occurs before tool execution for strategic decision making
    """
    def __init__(self,
                 user_id: str,
                 tools: List[BaseTool],
                 mcp_ids: List[str]):
        self.tools = tools
        self.user_id = user_id
        self.mcp_ids = mcp_ids
        self.mcp_manager: MCPManager = None

        self.mcp_tools = []
        self.conversation_model = ModelManager.get_conversation_model()
        self.tool_call_model = ModelManager.get_tool_invocation_model()

    async def setup_mcp_tools(self):
        if not self.mcp_manager:
            mcp_servers = []
            for mcp_id in self.mcp_ids:
                mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
                mcp_servers.append(mcp_server)
                self.mcp_servers = mcp_servers
            self.mcp_manager = MCPManager(convert_mcp_config(mcp_servers))

        return await self.mcp_manager.get_mcp_tools()

    async def _plan_agent_actions(self, messages: List[BaseMessage]):
        structured_response_agent = StructuredResponseAgent(response_format=PlanToolFlow)

        call_messages: List[BaseMessage] = []
        call_messages.extend(messages)

        if isinstance(call_messages[0], SystemMessage):
            call_messages[0] = SystemMessage(
                content=PLAN_CALL_TOOL_PROMPT.format(user_query=messages[-1].content,
                                                     tools_info="\n\n".join([str(tool.args_schema.model_dump()) for tool in self.tools + self.mcp_tools])))
        else:
            call_messages.insert(0, SystemMessage(content=PLAN_CALL_TOOL_PROMPT.format(user_query=messages[-1].content, tools_info="\n\n".join([str(tool_schema) for tool_schema in self.plugin_tools_schema + self.mcp_tools_schema]))))

        response = structured_response_agent.get_structured_response(call_messages)

        try:
            content = json.loads(response.content)
            self.agent_plans = content
            return content
        except Exception as err:
            # Send the error message for parsing model output
            fix_message = HumanMessage(
                content=FIX_JSON_PROMPT.format(json_content=response.content, json_error=str(err)))
            fix_response = await self.conversation_model.ainvoke([fix_message])

            try:
                fix_content = json.loads(fix_response.content)
                self.agent_plans = fix_content
                # Send the completion message for JSON data repair
                return fix_content
            except Exception as fix_err:
                # Send the message for irreparable JSON data
                raise ValueError(fix_err)

    async def _execute_agent_actions(self, agent_plans):
        tool_call_model = self.tool_call_model.bind_tools(self.tools + self.mcp_tools)

        tool_results: List[BaseMessage] = []
        for step, plan in agent_plans.items():
            if plan[0].get("tool_name") == "call_user":
                tool_results.append(AIMessage(content=str(plan)))
                break

            # Prepare different prompts for each call
            call_tool_messages = []
            system_message = HumanMessage(content=SINGLE_PLAN_CALL_PROMPT.format(plan_actions=str(plan)))
            call_tool_messages.append(system_message)
            call_tool_messages.extend(tool_results)

            response = await tool_call_model.ainvoke(call_tool_messages)
            # Determine if there are tools available for calling
            if response.tool_calls:
                return response
            else:
                # Send no tools available event to main agent
                ai_message = AIMessage(content="No available tools found")

            tool_messages = await self._execute_tool(ai_message)
            tool_results.append(ai_message)
            tool_results.extend(tool_messages)

        return tool_results

    async def _execute_tool(self, message: AIMessage):
        """Tool execution - sub-agent responsible for specific tool execution"""
        tool_calls = message.tool_calls
        tool_messages: List[BaseMessage] = []

        for tool_call in tool_calls:
            is_mcp_tool, use_tool = self._find_tool_use(tool_call["name"])
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            try:
                if hasattr(use_tool, "coroutine") and use_tool.coroutine is not None:
                    # Determine if user personal configuration needs to be added
                    if is_mcp_tool:
                        personal_config = await MCPUserConfigService.get_mcp_user_config(self.user_id, self._get_mcp_id_by_tool(tool_name))
                        tool_args.update(personal_config)

                    tool_result, _ = await use_tool.coroutine(**tool_args)
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

    async def astream(self, messages: List[BaseMessage]):
        await self.setup_mcp_tools()

        agent_plans = await self._plan_agent_actions(messages)
        if agent_plans:
            tool_results = await self._execute_agent_actions(agent_plans)
        else:
            tool_results = []

        messages.extend(tool_results)
        try:
            response_content = ""
            async for chunk in self.conversation_model.astream(messages):
                if chunk.content:
                    response_content += chunk.content
                    yield {
                        "content": chunk.content
                    }
        except Exception as err:
            logger.error(f"LLM stream error: {err}")


    async def ainvoke(self, messages: List[BaseMessage]):
        await self.setup_mcp_tools()

        agent_plans = await self._plan_agent_actions(messages)
        if agent_plans:
            tool_results = await self._execute_agent_actions(agent_plans)
        else:
            tool_results = []

        messages.extend(tool_results)
        response = await self.conversation_model.ainvoke(messages)
        return response.content

    def _get_mcp_id_by_tool(self, tool_name):
        for server in self.mcp_servers:
            if tool_name in server["tools"]:
                return server["mcp_server_id"]
        return None

    def _find_tool_use(self, tool_name):
        if tool_name in [tool.name for tool in self.tools]:
            return True, self.tools[tool_name]
        elif tool_name in [tool.name for tool in self.mcp_tools]:
            return True, self.mcp_tools[tool_name]
        return False, None