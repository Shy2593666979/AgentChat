from services.rag.es_client import client as es_client
from services.rag.milvus_client import client as milvus_client
from services.rewrite.query_write import query_rewriter


class MixRetrival:

    @classmethod
    async def retrival_milvus_documents(cls, query, knowledges_id):
        documents = []
        for knowledge_id in knowledges_id:
            documents += await milvus_client.search(query, knowledge_id)

        return documents

    @classmethod
    async def retrival_es_documents(cls, query, knowledges_id):
        documents = []
        for knowledge_id in knowledges_id:
            documents += await es_client.search_documents(query, knowledge_id)

        return documents

    @classmethod
    async def mix_retrival_documents(cls, query_list, knowledges_id):
        es_documents = []
        milvus_documents = []
        for query in query_list:
            es_documents += await cls.retrival_es_documents(query, knowledges_id)
            milvus_documents += await cls.retrival_milvus_documents(query, knowledges_id)

        return es_documents, milvus_documents
