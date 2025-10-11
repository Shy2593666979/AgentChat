from agentchat.services.rag.vector_db.milvus_client import MilvusClient
from agentchat.services.rag.vector_db.chroma_client import ChromaClient
from agentchat.services.rag.vector_db.milvus_lite_client import MilvusLiteClient
from agentchat.settings import app_settings

milvus_client = None
if app_settings.rag.vector_db.get("mode") == "chroma":
    milvus_client = ChromaClient()
elif app_settings.rag.vector_db.get("mode") == "lite":
    milvus_client = MilvusLiteClient()
else:
    milvus_client = MilvusClient()