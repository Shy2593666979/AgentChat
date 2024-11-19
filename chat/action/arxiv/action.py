from typing import Type, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_community.utilities import ArxivAPIWrapper

arxiv_wrapper = ArxivAPIWrapper()

class ArxivInput(BaseModel):
    query: str = Field(description='用户输入的问题')


class ArxivTool(BaseTool):
    name = 'arxiv'
    description = '为用户提供Arxiv上的论文'
    args_schema: Type[BaseModel] = ArxivInput

    def _run(self, query: str):
        return get_arxiv(query)

# 支持Function Call的模型
def get_arxiv(query: str):
    """为用户提供Arxiv上的论文"""
    docs = arxiv_wrapper.run(query)
    return docs
