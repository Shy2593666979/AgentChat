import json
import time
from typing import Optional

from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.knowledge_file import KnowledgeFileService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.mars import Mars_Generate_Query_Prompt
from agentchat.services.mars.events import get_mars_writer, progress
from agentchat.services.rag.handler import RagHandler


@tool(parse_docstring=True)
async def query_knowledge(query: str, user_id: Optional[str] = None):
    """
    根据用户的所有知识库进行检索生成一篇报告

    Args:
        query: 用户检索知识库的问题信息
        user_id: 当前用户ID，默认为None

    Returns:
        用户问题在知识库中有关的信息
    """
    writer = get_mars_writer()
    writer(progress("读取可访问的知识库与文档"))

    chat_model = ModelManager.get_chat_model()

    knowledges = await KnowledgeService.select_knowledge(user_id)

    knowledges_id = [knowledge["id"] for knowledge in knowledges]
    knowledge_files = []
    for knowledge_id in knowledges_id:
        knowledge_files.extend(await KnowledgeFileService.get_knowledge_file(knowledge_id))

    writer(progress(f"读取了 {len(knowledges)} 个知识库、{len(knowledge_files)} 个文档", "complete"))
    generate_query = [query]
    response = await chat_model.ainvoke(Mars_Generate_Query_Prompt.format(file_names="\n".join([file["file_name"] for file in knowledge_files])))
    try:
        content = json.loads(response.content)
        generate_query.extend(content.get("query", []))

    except Exception as err:
        logger.error(f"Except JSON Error: {err}")

    documents = []
    for search_query in generate_query:
        writer(progress(f"检索知识：{search_query}"))
        document = await RagHandler.retrieve_ranked_documents(search_query, knowledges_id, knowledges_id)
        documents.append(document)

    writer(progress("知识检索完成，正在整理报告", "complete"))
    messages = [HumanMessage(content=query), SystemMessage(content="\n\n".join(documents))]

    async for chunk in chat_model.astream(messages):
        writer(
            {
                "type": "response_chunk",
                "time": time.time(),
                "data": chunk.content,
            }
        )
