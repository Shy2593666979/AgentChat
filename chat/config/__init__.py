import yaml
import os

# 将用户配置的LLM进行设置全局变量
LLM_OPENAI_BASE_URL = ""
LLM_OPENAI_API_KEY = ""
LLM_OPENAI_MODEL = ""

# 将用户配置的langfuse进行设置全局变量
LANGFUSE_HOST = ""
LANGFUSE_USER_ID = ""
LANGFUSE_CHAT_TRACE_NAME = ""
LANGFUSE_FUNCTION_TRACE_NAME = ""
LANGFUSE_SECRET_KEY = ""
LANGFUSE_PUBLIC_KEY = ""

# 将用户配置的tool进行设置全局变量
TOOL_WEATHER_BASE_URL = ""
TOOL_WEATHER_API_KEY = ""
TOOL_DELIVERY_BASE_URL = ""
TOOL_DELIVERY_API_KEY = ""
TOOL_GOOGLE_API_KEY = ""

# 将用户配置的embedding model进行设置全局变量
RAG_EMBEDDING_CHOOSE = ""
RAG_EMBEDDING_OPENAI_MODEL = ""
RAG_EMBEDDING_OPENAI_BASE_URL = ""
RAG_EMBEDDING_OPENAI_API_KEY = ""
RAG_EMBEDDING_DEFAULT_MODEL = ""
RAG_EMBEDDING_DEFAULT_CACHE_DIR = ""

# 将用户配置的reranker进行设置全局变量
RAG_RERANK_CHOOSE = ""
RAG_RERANK_COHERE_API_KEY = ""
RAG_RERANK_DEFAULT_MODEL = ""
RAG_RERANK_DEFAULT_CACHE_DIR = ""

# 更新本地config文件
def update_yaml_file(data):
    data_dict = yaml.safe_load(data)

    with open("config/system_config.yaml", 'w', encoding='utf-8') as file:
        yaml.dump(data_dict, file , default_flow_style=False)

# 更新config文件中的全局变量
def update_user_config():
    with open("config/system_config.yaml", 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    global LLM_OPENAI_API_KEY, LLM_OPENAI_BASE_URL, LLM_OPENAI_MODEL
    global LANGFUSE_CHAT_TRACE_NAME, LANGFUSE_FUNCTION_TRACE_NAME, LANGFUSE_HOST, LANGFUSE_USER_ID, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
    global TOOL_WEATHER_API_KEY, TOOL_DELIVERY_API_KEY, TOOL_WEATHER_BASE_URL, TOOL_DELIVERY_BASE_URL, TOOL_GOOGLE_API_KEY
    global RAG_EMBEDDING_CHOOSE, RAG_EMBEDDING_OPENAI_MODEL, RAG_EMBEDDING_OPENAI_BASE_URL, RAG_EMBEDDING_OPENAI_API_KEY, RAG_EMBEDDING_DEFAULT_MODEL, RAG_EMBEDDING_DEFAULT_CACHE_DIR
    global RAG_RERANK_CHOOSE, RAG_RERANK_DEFAULT_MODEL, RAG_RERANK_DEFAULT_CACHE_DIR, RAG_RERANK_COHERE_API_KEY

    LLM_OPENAI_MODEL = config['llm']['openai']['model']
    LLM_OPENAI_API_KEY = config['llm']['openai']['api_key']
    LLM_OPENAI_BASE_URL = config['llm']['openai']['base_url']

    LANGFUSE_USER_ID = config['langfuse']['user_id']
    LANGFUSE_CHAT_TRACE_NAME = config['langfuse']['chat_trace_name']
    LANGFUSE_FUNCTION_TRACE_NAME = config['langfuse']['function_trace_name']
    LANGFUSE_SECRET_KEY = config['langfuse']['secret_key']
    LANGFUSE_PUBLIC_KEY = config['langfuse']['public_key']
    LANGFUSE_HOST = config['langfuse']['host']

    TOOL_WEATHER_BASE_URL = config['tool']['weather']['base_url']
    TOOL_WEATHER_API_KEY = config['tool']['weather']['api_key']
    TOOL_DELIVERY_BASE_URL = config['tool']['delivery']['base_url']
    TOOL_DELIVERY_API_KEY = config['tool']['delivery']['api_key']
    TOOL_GOOGLE_API_KEY = config['tool']['google']['api_key']

    RAG_EMBEDDING_CHOOSE = config['rag']['embedding']['choose']
    RAG_EMBEDDING_OPENAI_API_KEY = config['rag']['embedding']['openai']['api_key']
    RAG_EMBEDDING_OPENAI_MODEL = config['rag']['embedding']['openai']['model']
    RAG_EMBEDDING_OPENAI_BASE_URL = config['rag']['embedding']['openai']['base_url']
    RAG_EMBEDDING_DEFAULT_CACHE_DIR = config['rag']['embedding']['default']['cache_dir']
    RAG_EMBEDDING_DEFAULT_MODEL = config['rag']['embedding']['default']['model']

    RAG_RERANK_CHOOSE = config['rag']['rerank']['choose']
    RAG_RERANK_COHERE_API_KEY = config['rag']['rerank']['cohere']['api_key']
    RAG_RERANK_DEFAULT_MODEL = config['rag']['rerank']['default']['model']
    RAG_RERANK_DEFAULT_CACHE_DIR = config['rag']['rerank']['default']['cache_dir']
