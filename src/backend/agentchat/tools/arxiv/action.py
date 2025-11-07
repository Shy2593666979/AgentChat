from langchain.tools import tool
from langchain_community.utilities import ArxivAPIWrapper

arxiv_wrapper = ArxivAPIWrapper()

@tool(parse_docstring=True)
def get_arxiv(query: str):
    """
    在 Arxiv 上为用户提供相关论文的信息。

    Args:
        query (str): 用户提供的搜索关键词。

    Returns:
        str: 与查询相关的论文文档。
    """
    return _get_arxiv(query)

def _get_arxiv(query: str):
    """为用户提供Arxiv上的论文"""
    docs = arxiv_wrapper.run(query)
    return docs
