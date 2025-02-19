from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from utils.helpers import check_or_create

def get_embeddings() -> Embeddings:

    # if userConfig.RAG_EMBEDDING_CHOOSE == "default":
    #     # 确保输入的地址有效
    #     check_or_create(userConfig.RAG_EMBEDDING_DEFAULT_CACHE_DIR)
    #
    #     embeddings = HuggingFaceEmbeddings(model_name=userConfig.RAG_EMBEDDING_DEFAULT_MODEL,
    #                                        cache_folder=userConfig.RAG_EMBEDDING_DEFAULT_CACHE_DIR)
    #
    # else:
    #     embeddings = OpenAIEmbeddings(model=userConfig.RAG_EMBEDDING_OPENAI_MODEL,
    #                                   base_url=userConfig.RAG_EMBEDDING_OPENAI_BASE_URL,
    #                                   api_key=userConfig.RAG_EMBEDDING_OPENAI_API_KEY)
    return None
    
