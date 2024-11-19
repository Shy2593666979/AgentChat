from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import TextSplitter


def markdown_loader(path: str, text_splitter: TextSplitter):
    loader = UnstructuredMarkdownLoader(path)

    result = loader.load_and_split(text_splitter=text_splitter)
    return result