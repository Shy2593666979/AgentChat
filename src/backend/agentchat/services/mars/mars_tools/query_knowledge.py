import time
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.core.models.manager import ModelManager
from agentchat.services.rag_handler import RagHandler


async def query_knowledge(query: str, user_id: Optional[str] = None):
    """
    根据用户的所有知识库进行检索生成一篇报告

    params:
        query: 用户检索知识库的问题信息

    return:
        用户问题在知识库中有关的信息
    """

    knowledges = await KnowledgeService.select_knowledge(user_id)

    knowledges_id = [knowledge["id"] for knowledge in knowledges]
    content = await RagHandler.retrieve_ranked_documents(query, knowledges_id, knowledges_id)

    conversation_model = ModelManager.get_conversation_model()

    messages = [HumanMessage(content=query), SystemMessage(content=content)]

    async for chunk in conversation_model.astream(messages):
        yield {
            "type": "response_chunk",
            "time": time.time(),
            "data": chunk.content
        }
