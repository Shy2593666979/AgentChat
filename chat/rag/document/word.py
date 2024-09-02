from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from langchain_community.document_loaders import UnstructuredWordDocumentLoader

def word_loader(path: str, text_splitter: TextSplitter):
    loader = UnstructuredWordDocumentLoader(path)

    result = loader.load_and_split(text_splitter=text_splitter)
    return result
    
# def word_loader(path: str, text_splitter: TextSplitter):
#     # 使用 python-docx 加载 Word 文档
#     doc = Document(path)

#     # 读取文档内容
#     pages = [p.text for p in doc.paragraphs]

#     result = text_splitter.split_documents(pages)

#     return result


