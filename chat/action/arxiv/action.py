from langchain.utilities import  ArxivAPIWrapper

arxiv_wrapper = ArxivAPIWrapper()

def arxiv_action(information: str):
    docs = arxiv_wrapper.run(information)
    return docs