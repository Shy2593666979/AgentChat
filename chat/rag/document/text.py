from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import TextSplitter


def text_loader(path: str, text_splitter: TextSplitter):
    loader = TextLoader(path)
    result = loader.load_and_split(text_splitter=text_splitter)

    return result