from typing import Optional

from agentchat.services.deepsearch.stream_graph import StreamingGraph
from langchain_core.messages import HumanMessage


async def deep_search(user_input: str, user_id: Optional[str] = None):
    """
     执行深度搜索，处理用户查询并返回深度搜索后的结果

    Args:
        user_input: 用户的搜索的信息
        user_id: 可选的用户标识，用于个性化搜索或权限验证

    Returns:
        返回深度搜索后的信息
    """
    messages = [HumanMessage(content=user_input)]

    stream_graph = StreamingGraph()

    for chunk in stream_graph.run_with_streaming(messages):
        yield chunk

