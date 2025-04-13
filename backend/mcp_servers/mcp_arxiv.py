from mcp.server.fastmcp import FastMCP
from langchain_community.utilities import ArxivAPIWrapper

arxiv_wrapper = ArxivAPIWrapper()

mcp = FastMCP("MCP-Arxiv")

@mcp.tool()
def get_arxiv(query: str):
    """为用户提供Arxiv上的论文

    Args:
        query: 用户问题
    """
    docs = arxiv_wrapper.run(query)
    return docs

if __name__ == "__main__":
    mcp.run(transport='stdio')