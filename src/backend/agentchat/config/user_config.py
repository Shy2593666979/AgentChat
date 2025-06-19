import yaml
import os

class UserConfig:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        self.USE_CAPTCHA = config['use_captcha']
        self.LLM_OPENAI_MODEL = config['llm']['openai']['model']
        self.LLM_OPENAI_API_KEY = config['llm']['openai']['api_key']
        self.LLM_OPENAI_BASE_URL = config['llm']['openai']['base_url']

        self.LANGFUSE_USER_ID = config['langfuse']['user_id']
        self.LANGFUSE_CHAT_TRACE_NAME = config['langfuse']['chat_trace_name']
        self.LANGFUSE_FUNCTION_TRACE_NAME = config['langfuse']['function_trace_name']
        self.LANGFUSE_SECRET_KEY = config['langfuse']['secret_key']
        self.LANGFUSE_PUBLIC_KEY = config['langfuse']['public_key']
        self.LANGFUSE_HOST = config['langfuse']['host']

        self.TOOL_WEATHER_BASE_URL = config['tool']['weather']['base_url']
        self.TOOL_WEATHER_API_KEY = config['tool']['weather']['api_key']
        self.TOOL_DELIVERY_BASE_URL = config['tool']['delivery']['base_url']
        self.TOOL_DELIVERY_API_KEY = config['tool']['delivery']['api_key']
        self.TOOL_GOOGLE_API_KEY = config['tool']['google']['api_key']

        self.RAG_INPUT_DIR = config['rag']['input_dir']
        
        self.RAG_EMBEDDING_CHOOSE = config['rag']['embedding']['choose']
        self.RAG_EMBEDDING_OPENAI_API_KEY = config['rag']['embedding']['openai']['api_key']
        self.RAG_EMBEDDING_OPENAI_MODEL = config['rag']['embedding']['openai']['model']
        self.RAG_EMBEDDING_OPENAI_BASE_URL = config['rag']['embedding']['openai']['base_url']
        self.RAG_EMBEDDING_DEFAULT_CACHE_DIR = config['rag']['embedding']['default']['cache_dir']
        self.RAG_EMBEDDING_DEFAULT_MODEL = config['rag']['embedding']['default']['model']

        self.RAG_RERANK_CHOOSE = config['rag']['rerank']['choose']
        self.RAG_RERANK_COHERE_MODEL = config['rag']['rerank']['cohere']['model']
        self.RAG_RERANK_COHERE_API_KEY = config['rag']['rerank']['cohere']['api_key']
        self.RAG_RERANK_DEFAULT_MODEL = config['rag']['rerank']['default']['model']
        self.RAG_RERANK_DEFAULT_CACHE_DIR = config['rag']['rerank']['default']['cache_dir']

    def reload_config(self):
        self.load_config()

    # 更新本地config文件
    def update_yaml_file(self, data: str):
        data_dict = yaml.safe_load(data)

        with open(self.config_file, 'w', encoding='utf-8') as file:
            yaml.dump(data_dict, file, default_flow_style=False)

    # 提供给前端展示给用户
    def get_user_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return yaml.dump(config, default_flow_style=False, default_style='"')


userConfig = UserConfig(config_file="config/user_config.yaml")

# # 将用户配置的LLM进行设置全局变量
# LLM_OPENAI_BASE_URL = ""
# LLM_OPENAI_API_KEY = ""
# LLM_OPENAI_MODEL = ""

# # 将用户配置的langfuse进行设置全局变量
# LANGFUSE_HOST = ""
# LANGFUSE_USER_ID = ""
# LANGFUSE_CHAT_TRACE_NAME = ""
# LANGFUSE_FUNCTION_TRACE_NAME = ""
# LANGFUSE_SECRET_KEY = ""
# LANGFUSE_PUBLIC_KEY = ""

# # 将用户配置的tool进行设置全局变量
# TOOL_WEATHER_BASE_URL = ""
# TOOL_WEATHER_API_KEY = ""
# TOOL_DELIVERY_BASE_URL = ""
# TOOL_DELIVERY_API_KEY = ""
# TOOL_GOOGLE_API_KEY = ""

# RAG_INPUT_DIR = ""

# # 将用户配置的embedding model进行设置全局变量
# RAG_EMBEDDING_CHOOSE = ""
# RAG_EMBEDDING_OPENAI_MODEL = ""
# RAG_EMBEDDING_OPENAI_BASE_URL = ""
# RAG_EMBEDDING_OPENAI_API_KEY = ""
# RAG_EMBEDDING_DEFAULT_MODEL = ""
# RAG_EMBEDDING_DEFAULT_CACHE_DIR = ""

# # 将用户配置的reranker进行设置全局变量
# RAG_RERANK_CHOOSE = ""
# RAG_RERANK_COHERE_MODEL = ""
# RAG_RERANK_COHERE_API_KEY = ""
# RAG_RERANK_DEFAULT_MODEL = ""
# RAG_RERANK_DEFAULT_CACHE_DIR = ""

# # 更新本地config文件
# def update_yaml_file(data: str):
#     data_dict = yaml.safe_load(data)

#     with open("config/user_config.yaml", 'w', encoding='utf-8') as file:
#         yaml.dump(data_dict, file, default_flow_style=False)

# # 初始化本地config 文件
# def init_user_config():
#     update_user_config()

# def get_user_config():
#     with open("config/user_config.yaml", 'r', encoding='utf-8') as file:
#         config = yaml.safe_load(file)
#     return yaml.dump(config, default_flow_style=False)

# # 更新config文件中的全局变量
# def update_user_config():
#     with open("config/user_config.yaml", 'r', encoding='utf-8') as file:
#         config = yaml.safe_load(file)

#     global LLM_OPENAI_API_KEY, LLM_OPENAI_BASE_URL, LLM_OPENAI_MODEL
#     global LANGFUSE_CHAT_TRACE_NAME, LANGFUSE_FUNCTION_TRACE_NAME, LANGFUSE_HOST, LANGFUSE_USER_ID, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
#     global TOOL_WEATHER_API_KEY, TOOL_DELIVERY_API_KEY, TOOL_WEATHER_BASE_URL, TOOL_DELIVERY_BASE_URL, TOOL_GOOGLE_API_KEY
#     global RAG_EMBEDDING_CHOOSE, RAG_EMBEDDING_OPENAI_MODEL, RAG_EMBEDDING_OPENAI_BASE_URL, RAG_EMBEDDING_OPENAI_API_KEY, RAG_EMBEDDING_DEFAULT_MODEL, RAG_EMBEDDING_DEFAULT_CACHE_DIR
#     global RAG_RERANK_CHOOSE, RAG_RERANK_DEFAULT_MODEL, RAG_RERANK_DEFAULT_CACHE_DIR, RAG_RERANK_COHERE_API_KEY, RAG_RERANK_COHERE_MODEL
#     global RAG_INPUT_DIR
    
#     LLM_OPENAI_MODEL = config['llm']['openai']['models']
#     LLM_OPENAI_API_KEY = config['llm']['openai']['api_key']
#     LLM_OPENAI_BASE_URL = config['llm']['openai']['base_url']

#     LANGFUSE_USER_ID = config['langfuse']['user_id']
#     LANGFUSE_CHAT_TRACE_NAME = config['langfuse']['chat_trace_name']
#     LANGFUSE_FUNCTION_TRACE_NAME = config['langfuse']['function_trace_name']
#     LANGFUSE_SECRET_KEY = config['langfuse']['secret_key']
#     LANGFUSE_PUBLIC_KEY = config['langfuse']['public_key']
#     LANGFUSE_HOST = config['langfuse']['host']

#     TOOL_WEATHER_BASE_URL = config['tool']['weather']['base_url']
#     TOOL_WEATHER_API_KEY = config['tool']['weather']['api_key']
#     TOOL_DELIVERY_BASE_URL = config['tool']['delivery']['base_url']
#     TOOL_DELIVERY_API_KEY = config['tool']['delivery']['api_key']
#     TOOL_GOOGLE_API_KEY = config['tool']['google']['api_key']

#     RAG_INPUT_DIR = config['rag']['input_dir']
    
#     RAG_EMBEDDING_CHOOSE = config['rag']['embedding']['choose']
#     RAG_EMBEDDING_OPENAI_API_KEY = config['rag']['embedding']['openai']['api_key']
#     RAG_EMBEDDING_OPENAI_MODEL = config['rag']['embedding']['openai']['models']
#     RAG_EMBEDDING_OPENAI_BASE_URL = config['rag']['embedding']['openai']['base_url']
#     RAG_EMBEDDING_DEFAULT_CACHE_DIR = config['rag']['embedding']['default']['cache_dir']
#     RAG_EMBEDDING_DEFAULT_MODEL = config['rag']['embedding']['default']['models']

#     RAG_RERANK_CHOOSE = config['rag']['rerank']['choose']
#     RAG_RERANK_COHERE_MODEL = config['rag']['rerank']['cohere']['models']
#     RAG_RERANK_COHERE_API_KEY = config['rag']['rerank']['cohere']['api_key']
#     RAG_RERANK_DEFAULT_MODEL = config['rag']['rerank']['default']['models']
#     RAG_RERANK_DEFAULT_CACHE_DIR = config['rag']['rerank']['default']['cache_dir']



