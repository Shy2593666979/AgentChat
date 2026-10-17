from typing import Optional

from langchain.tools import tool
from langchain_core.messages import HumanMessage

from agentchat.services.deepsearch.stream_graph import StreamingGraph
from agentchat.services.mars.events import get_mars_writer, stream_search_report


@tool(parse_docstring=True)
async def deep_search(user_input: str, user_id: Optional[str] = None):
    """
     执行深度搜索，处理用户查询并返回深度搜索后的结果

    Args:
        user_input: 用户的搜索的信息
        user_id: 当前用户ID，默认为None

    Returns:
        返回深度搜索后的信息
    """
    writer = get_mars_writer()
    messages = [HumanMessage(content=user_input)]

    stream_graph = StreamingGraph()

    return await stream_search_report(stream_graph, messages, writer)

