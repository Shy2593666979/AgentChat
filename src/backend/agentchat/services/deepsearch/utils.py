from typing import Any, Dict, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    从消息中获取研究主题。
    """
    # 检查请求是否有历史记录并将消息合并为单个字符串
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """
    创建Vertex AI搜索URL（非常长）到带有唯一ID的短URL的映射。
    确保每个原始URL获得一个一致的缩短形式，同时保持唯一性。
    """
    prefix = f"https://vertexaisearch.cloud.google.com/id/"
    urls = [site.web.uri for site in urls_to_resolve]

    # 创建一个字典，将每个唯一URL映射到其第一次出现的索引
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """
    根据开始和结束索引在文本字符串中插入引用标记。

    参数:
        text (str): 原始文本字符串。
        citations_list (list): 字典列表，每个字典包含'start_index'、'end_index'和
                              'segment_string'（要插入的标记）。
                              假定索引是针对原始文本的。

    返回:
        str: 插入引用标记后的文本。
    """
    # 按end_index降序排序引用。
    # 如果end_index相同，则按start_index降序进行二次排序。
    # 这确保了字符串末尾的插入不会影响
    # 仍需处理的字符串早期部分的索引。
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # 这些索引指的是*原始*文本中的位置，
        # 但由于我们从末尾开始迭代，它们对于插入仍然有效
        # 相对于已处理的字符串部分。
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        # 在原始end_idx位置插入引用标记
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    从Gemini模型的响应中提取和格式化引用信息。

    此函数处理响应中提供的基础元数据，以构建引用对象列表。
    每个引用对象包括它所指的文本段的开始和结束索引，
    以及包含指向支持网页块的格式化Markdown链接的字符串。

    参数:
        response: 来自Gemini模型的响应对象，预期具有包括
                 `candidates[0].grounding_metadata`的结构。
                 它还依赖于其作用域中有一个可用的`resolved_map`
                 来将块URI映射到已解析的URL。

    返回:
        list: 字典列表，其中每个字典表示一个引用，
              具有以下键:
              - "start_index" (int): 原始文本中被引用段的起始字符索引。
                                    如果未指定，默认为0。
              - "end_index" (int): 被引用段结束后的字符索引（不包括）。
              - "segments" (list[str]): 每个基础块的单独Markdown格式链接列表。
              - "segment_string" (str): 引用的所有Markdown格式链接的连接字符串。
              如果找不到有效的候选项或基础支持，或者缺少基本数据，则返回空列表。
    """
    citations = []

    # 确保响应和必要的嵌套结构存在
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # 确保段信息存在
        if not hasattr(support, "segment") or support.segment is None:
            continue  # 如果段信息缺失，跳过此支持

        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # 确保end_index存在以形成有效段
        if support.segment.end_index is None:
            continue  # 如果end_index缺失则跳过，因为它很关键

        # 为切片/范围目的将end_index加1使其成为排他性结束
        # （假设API提供包含性end_index）
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],
                            "short_url": resolved_url,
                            "value": chunk.web.uri,
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # 处理chunk、web、uri或resolved_map可能有问题的情况
                    # 为简单起见，我们将跳过添加这个特定的段链接
                    # 在生产系统中，您可能想要记录这个问题。
                    pass
        citations.append(citation)
    return citations