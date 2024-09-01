import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.document.text import text_loader
from rag.document.pdf import pdf_loader
from rag.document.word import word_loader
from rag.document.excel import excel_loader
from rag.document.markdown import markdown_loader
from rag.embedding import get_embeddings
from loguru import logger
from tqdm import tqdm

class_document = {
    "md": markdown_loader,
    "xlsx": excel_loader,
    "docx": word_loader,
    "pdf": pdf_loader,
    "txt": text_loader
}

embeddings = get_embeddings()


vector_store = Chroma(collection_name="agentchat", embedding_function=embeddings)

# 使用文本分割器
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)


def load_folder_all_file(folder_path: str):
    if not os.path.exists(folder_path):
        logger.error("RAG input dir not exists")
        raise ValueError("RAG 输入文件夹不存在")

    for file in tqdm(os.listdir(folder_path)):
        file_name = os.path.basename(file)
        
        class_file = file_name.split('.')[-1]

        # 只允许加载五种文本类型的数据，其他跳过
        if class_file in class_document:
            document_function = class_document[class_file]
            data = document_function(path=os.path.join(folder_path, file_name), text_splitter=text_loader)
            vector_store.add_documents(data)