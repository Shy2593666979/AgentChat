from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import TextSplitter


def pdf_loader(path: str, text_splitter: TextSplitter):
    loader = PyPDFLoader(path)

    result = loader.load_and_split(text_splitter=text_splitter)
    return result