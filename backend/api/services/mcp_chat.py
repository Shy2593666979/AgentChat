import asyncio

from api.services.history import HistoryService
from prompts.llm_prompt import MCP_TOOL_TEMPLATE
from services.mcp.mcp_manager import MCPManager
from core.models.anthropic import DeepAsyncAnthropic
from api.services.llm import LLMService
from services.rag_handler import RagHandler


class MCPChatAgent:
    def __init__(self, **kwargs):
        self.mcp_servers_id = kwargs.get("mcp_servers_id")
        self.llm_id = kwargs.get("llm_id")
        self.use_embedding = kwargs.get("use_embedding")
        self.knowledges_id = kwargs.get("knowledges_id")

        self.deep_anthropic = self._init_Anthropic()
        self.mcp_manager = self._init_MCP_Manager()
        self._init_MCP_Server()

    def _init_Anthropic(self) -> DeepAsyncAnthropic:
        llm_config = LLMService.get_llm_by_id(self.llm_id)
        return DeepAsyncAnthropic(**llm_config)

    def _init_MCP_Manager(self) -> MCPManager:
        return MCPManager(self.deep_anthropic)

    def _init_MCP_Server(self):
        for server_id in self.mcp_servers_id:
            # MCP_Server.get_server(server_id) 获得server_id 对应的脚本Path
            server_path = ""
            self.mcp_manager.enter_mcp_server(server_path)

    async def ainvoke(self, user_input: str, dialog_id: str, stream: bool=False):
        # 并发获取History 和 RAG Message
        history_messages, recall_knowledge_data = await asyncio.gather(
            self.get_history_message(user_input, dialog_id),
            RagHandler.rag_query(user_input, self.knowledges_id)
        )
        # mcp_tool_query = MCP_TOOL_TEMPLATE.format(query=user_input, history=history_message)
        mcp_tool_messages = history_messages.copy()
        mcp_response = await self.mcp_manager.process_query(mcp_tool_messages)

        # 合并Tool Message 和 RAG Message
        mcp_response.append({"role": "user", "content": recall_knowledge_data})
        if stream:
            return self._stream_response(mcp_response)
        else:
            return await self._normal_response(mcp_response)

    async def get_history_message(self, user_input: str, dialog_id: str, top_k: int = 5) :
        # 如果开启Embedding，默认走RAG检索聊天记录
        if self.use_embedding:
            messages = await self._retrieval_history(user_input, dialog_id, top_k)
            return messages
        else:
            messages = await self._direct_history(dialog_id, top_k)

            result = []
            for message in messages:
                result.append(message.to_json())
            return result

    async def _stream_response(self, messages):
        async for text in self.deep_anthropic.ainvoke_stream(messages):
            yield text

    async def _normal_response(self, messages):
        response = self.deep_anthropic.ainvoke(messages)
        return response


    async def _direct_history(self, dialog_id: str, top_k: int):
        messages = HistoryService.select_history(dialog_id, top_k)
        return messages

    async def _retrieval_history(self, user_input: str, dialog_id: str, top_k: int):
        messages = await RagHandler.rag_query(user_input, dialog_id, 0.6, top_k, False)
        return messages



