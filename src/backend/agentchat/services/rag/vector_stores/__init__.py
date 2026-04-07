from agentchat.services.rag.vector_stores.milvus import MilvusClient
from agentchat.services.rag.vector_stores.chroma import ChromaClient
from agentchat.services.rag.vector_stores.milvus_lite import MilvusLiteClient
from agentchat.settings import app_settings

milvus_client = None
if app_settings.rag.vector_db.get("mode") == "chroma":
    milvus_client = ChromaClient()
elif app_settings.rag.vector_db.get("mode") == "lite":
    milvus_client = MilvusLiteClient()
else:
    milvus_client = MilvusClient()