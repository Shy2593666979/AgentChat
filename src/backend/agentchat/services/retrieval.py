from agentchat.services.rag.es_client import client as es_client
from agentchat.services.rag.vector_db import milvus_client


class MixRetrival:

    @classmethod
    async def retrival_milvus_documents(cls, query, knowledges_id, search_field):
        """从Milvus检索文档"""
        documents = []
        queries = query if isinstance(query, list) else [query]

        for query in queries:
            for knowledge_id in knowledges_id:
                if search_field == "summary":
                    documents += await milvus_client.search_summary(query, knowledge_id)
                else:
                    documents += await milvus_client.search(query, knowledge_id)

        return documents

    @classmethod
    async def retrival_es_documents(cls, query, knowledges_id, search_field):
        """从Elasticsearch检索文档"""
        documents = []
        queries = query if isinstance(query, list) else [query]

        for query in queries:
            for knowledge_id in knowledges_id:
                if search_field == "summary":
                    documents += await es_client.search_documents_summary(query, knowledge_id)
                else:
                    documents += await es_client.search_documents(query, knowledge_id)

        return documents

    @classmethod
    async def mix_retrival_documents(cls, query_list, knowledges_id, search_field):
        es_documents = []
        milvus_documents = []
        for query in query_list:
            es_documents += await cls.retrival_es_documents(query, knowledges_id, search_field)
            milvus_documents += await cls.retrival_milvus_documents(query, knowledges_id, search_field)

        return es_documents, milvus_documents
