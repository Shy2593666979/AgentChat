from config import user_config
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from utils.helpers import check_or_create

def get_embeddings() -> Embeddings:
    
    if user_config.RAG_EMBEDDING_CHOOSE == "default":
        # 确保输入的地址有效
        check_or_create(user_config.RAG_RERANK_DEFAULT_CACHE_DIR)
        
        embeddings = HuggingFaceEmbeddings(model_name=user_config.RAG_EMBEDDING_DEFAULT_MODEL,
                                           cache_folder=user_config.RAG_RERANK_DEFAULT_CACHE_DIR)
        
    else:
        embeddings = OpenAIEmbeddings(model=user_config.RAG_EMBEDDING_OPENAI_MODEL,
                                      base_url=user_config.RAG_EMBEDDING_OPENAI_BASE_URL,
                                      api_key=user_config.RAG_EMBEDDING_OPENAI_API_KEY)
    return embeddings
    
