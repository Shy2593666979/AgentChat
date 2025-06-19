import asyncio

from langchain_core.tools import BaseTool
from agentchat.services.mcp.multi_client import MultiServerMCPClient
from loguru import logger

class MCPManager:
    def __init__(self, timeout=10):
        self.multi_server_client = MultiServerMCPClient()

        self.timeout = timeout

    async def connect_mcp_servers(self, mcp_servers: list):
        # 如果出现连接不上的mcp server 直接略过
        is_all_not_connect = True
        for server in mcp_servers:
            try:
                if server["type"] == "sse":
                    await self.multi_server_client.connect_to_sse_server(server["server_name"], url=server["url"], timeout=self.timeout)
                elif server["type"] == "websocket":
                    await self.multi_server_client.connect_to_websocket_server(server["server_name"], url=server["url"], timeout=self.timeout)
                else:
                    # TODO: 添加stdio方式
                    pass
                is_all_not_connect = False
            except Exception as err:
                logger.info(f"Connect mcp servers {server['server_name']} Error: {err}")
        if is_all_not_connect:
            await self.multi_server_client.aclose()

    # async def connect_sse_servers(self, mcp_servers: list):
    #     try:
    #         for server in mcp_servers:
    #             await self.multi_server_client.connect_to_sse_server(server["server_name"], url=server["url"], timeout=self.timeout)
    #     except Exception as err:
    #         logger.info(f"Connect sse servers Error: {err}")
    #         await self.multi_server_client.aclose()
    #
    # async def connect_stdio_servers(self, mcp_servers: list):
    #     pass
    #
    # async def connect_websocket_servers(self, mcp_servers: list):
    #     try:
    #         for server in mcp_servers:
    #             await self.multi_server_client.connect_to_websocket_server(server["server_name"], url=server["url"])
    #     except Exception as err:
    #         logger.info(f"Connect websocket servers Error: {err}")
    #         await self.multi_server_client.aclose()

    async def get_mcp_tools(self) -> list[BaseTool]:
        mcp_tools = self.multi_server_client.get_tools()
        return mcp_tools

    async def show_mcp_tools(self) -> dict:
        try:
            server_name_tools = await self.multi_server_client.show_tools()
            result = {}
            for key, tools in server_name_tools.items():
                tool_list = []
                for tool in tools:
                    # TODO: 基于LangChain的Tool Sdk修改，提取schema交给frontend
                    # args_schema = tool.args_schema.model_json_schema()
                    # input_schema = args_schema["properties"]["input_schema"]["default"]
                    input_schema = tool.args_schema
                    tool_dict = {
                        'name': tool.name,
                        'description': tool.description,
                        'input_schema': input_schema
                    }
                    tool_list.append(tool_dict)
                result[key] = tool_list
        except Exception as err:
            result = {}
            logger.info(f"获取MCP 服务工具列表出错: {err}")
        finally:
            await self.multi_server_client.aclose()
        return result

    async def call_mcp_tools(self, mcp_tools_args, is_concurrent=True):
        tool_results = []
        callable_tools = {}
        try:
            # 获取工具列表
            mcp_tools = self.multi_server_client.get_tools()
            for tool in mcp_tools:
                callable_tools[tool.name] = tool
            # 异步并发
            if is_concurrent:
                # 创建异步任务列表
                tasks = []
                for tool_args in mcp_tools_args:
                    tool_name = tool_args["tool_name"]
                    tool_args = tool_args["tool_args"]
                    # 创建异步任务
                    task = asyncio.create_task(callable_tools[tool_name].coroutine(**tool_args))
                    tasks.append(task)
                # 并发执行所有任务
                for task in asyncio.as_completed(tasks):
                    try:
                        result = await task
                        tool_results.append(result)
                    except Exception as e:
                        logger.error(f"执行工具时出错: {e}")
            else:
                for tool_args in mcp_tools_args:
                    tool_name = tool_args["tool_name"]
                    tool_args = tool_args["tool_args"]
                    try:
                        result = await callable_tools[tool_name].coroutine(**tool_args)
                        tool_results.append(result)
                    except Exception as e:
                        tool_results.append(f"执行工具 {tool_name} 时出错: {e}")
                        logger.error(f"执行工具 {tool_name} 时出错: {e}")

        except Exception as err:
            logger.error(f"调用工具发生错误：{err}")
        finally:
            await self.multi_server_client.aclose()
        return tool_results
