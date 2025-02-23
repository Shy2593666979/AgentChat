
from services.rag.parser import doc_parser
from services.retrieval import MixRetrival
from services.rewrite.query_write import query_rewriter
from services.rag.es_client import client as es_client
from services.rag.milvus_client import client as milvus_client
from services.rag.rerank import Reranker
from settings import app_settings

class RagHandler:

    @classmethod
    async def query_rewrite(cls, query):
        query_list = await query_rewriter.rewrite(query)
        return query_list

    @classmethod
    async def index_milvus_documents(cls, collection_name, file_id, file_path, knowledge_id):
        chunks = await doc_parser.parse_doc_into_chunks(file_id, file_path, knowledge_id)
        await milvus_client.insert(collection_name, chunks)

    @classmethod
    async def index_es_documents(cls, index_name, file_id, file_path, knowledge_id):
        chunks = await doc_parser.parse_doc_into_chunks(file_id, file_path, knowledge_id)
        await es_client.index_documents(index_name, chunks)

    @classmethod
    async def mix_retrival_documents(cls, query_list, knowledges_id):
        es_documents, milvus_documents = await MixRetrival.mix_retrival_documents(query_list, knowledges_id)

        es_documents.sort(key=lambda x: x.score, reverse=True)
        milvus_documents.sort(key=lambda x: x.score, reverse=True)

        documents = es_documents[:5] + milvus_documents[:5]
        return documents

    @classmethod
    async def rag_query(cls, query, knowledges_id, min_score: float=None, top_k: int=None):
        """
            处理 RAG 流程：查询重写、文档检索、重排序、结果过滤和拼接。

            参数:
                query (str): 用户查询。
                knowledges_id (str): 知识库 ID。
                min_score (float): 文档最低分数阈值，默认为配置中的值。
                skip_docs (int): 跳过前 N 个文档，默认为 3。

            返回:
                str: 拼接后的最终结果。
            """
        if min_score is None:
            min_score = app_settings.rag.get('min_score')
        if top_k is None:
            top_k = app_settings.rag.get('top_k')

        # 查询重写
        rewritten_queries = await cls.query_rewrite(query)

        # 文档检索
        retrieved_documents = await cls.mix_retrival_documents(rewritten_queries, knowledges_id)

        # 准备重排序的文档内容
        documents_to_rerank = [doc.content for doc in retrieved_documents]

        # 文档重排序
        reranked_docs = await Reranker.rerank_documents(query, documents_to_rerank)

        # 过滤结果
        filtered_results = []
        if len(reranked_docs) > top_k:
            for doc in reranked_docs[:top_k]:
                if doc.score >= min_score:
                    filtered_results.append(doc)

        # 处理空结果
        if not filtered_results:
            return "No relevant documents found."

        # 拼接最终结果
        final_result = "\n".join(result.content for result in filtered_results)
        return final_result

    @classmethod
    async def delete_documents_es_milvus(cls, file_id, knowledge_id):
        await es_client.delete_documents(file_id, knowledge_id)
        await milvus_client.delete_by_file_id(file_id, knowledge_id)
