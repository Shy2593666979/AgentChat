import json
import time
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from agentchat.api.services.knowledge import KnowledgeService
from agentchat.api.services.knowledge_file import KnowledgeFileService
from agentchat.core.models.manager import ModelManager
from agentchat.prompts.mars import Mars_Generate_Query_Prompt
from agentchat.services.rag_handler import RagHandler


async def query_knowledge(query: str, user_id: Optional[str] = None):
    """
    根据用户的所有知识库进行检索生成一篇报告

    params:
        query: 用户检索知识库的问题信息

    return:
        用户问题在知识库中有关的信息
    """
    conversation_model = ModelManager.get_conversation_model()

    knowledges = await KnowledgeService.select_knowledge(user_id)

    knowledges_id = [knowledge["id"] for knowledge in knowledges]
    knowledge_files = []
    for knowledge_id in knowledges_id:
        knowledge_files.extend(await KnowledgeFileService.get_knowledge_file(knowledge_id))

    generate_query = [query]
    response = await conversation_model.ainvoke(Mars_Generate_Query_Prompt.format(file_names="\n".join([file["file_name"] for file in knowledge_files])))
    try:
        content = json.loads(response.content)
        generate_query.extend(content.get("query", []))

    except Exception as err:
        logger.error(f"Except JSON Error: {err}")

    documents = []
    for query in generate_query:
        document = await RagHandler.retrieve_ranked_documents(query, knowledges_id, knowledges_id)
        documents.append(document)

    messages = [HumanMessage(content=query), SystemMessage(content="\n\n".join(documents))]

    async for chunk in conversation_model.astream(messages):
        yield {
            "type": "response_chunk",
            "time": time.time(),
            "data": chunk.content
        }
