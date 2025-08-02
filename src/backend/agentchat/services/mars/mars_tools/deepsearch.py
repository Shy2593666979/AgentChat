import time
from typing import Optional

from agentchat.services.deepsearch.stream_graph import StreamingGraph
from langchain_core.messages import HumanMessage


async def deep_search(user_input: str, user_id: Optional[str] = None):
    """
     执行深度搜索，处理用户查询并返回深度搜索后的结果

    Args:
        user_input(必选): 用户的搜索的信息
        user_id(可选): 可选的用户标识，用于个性化搜索或权限验证

    Returns:
        返回深度搜索后的信息
    """
    messages = [HumanMessage(content=user_input)]

    stream_graph = StreamingGraph()

    async for chunk in stream_graph.run_with_streaming(messages):
        chunk_type = chunk.get('type', 'unknown')
        node = chunk.get('node', 'unknown')
        content = chunk.get('content', '')

        event_data = {
            "type": "response_chunk",
            "time": time.time(),
            "data": ""
        }
        if chunk_type == "streaming":
            event_data["data"] = content
        elif chunk_type in ["start", "complete", "error"]:
            emoji = {"start": "🚀", "complete": "✅", "error": "❌"}[chunk_type]
            event_data["data"] = f"\n #### {emoji} {content}"
        elif chunk_type == "final_result":
            event_data["data"] = f""
        yield event_data

