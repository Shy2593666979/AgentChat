from loguru import logger
from typing import Optional
from agentchat.services.retrieval import MixRetrival
from agentchat.services.rewrite.query_write import query_rewriter
from agentchat.services.rag.es_client import client as es_client
from agentchat.services.rag.vector_db import milvus_client
from agentchat.services.rag.rerank import Reranker
from agentchat.settings import app_settings

class RagHandler:

    @classmethod
    async def query_rewrite(cls, query):
        query_list = await query_rewriter.rewrite(query)
        return query_list

    @classmethod
    async def index_milvus_documents(cls, collection_name, chunks):
        await milvus_client.insert(collection_name, chunks)

    @classmethod
    async def index_es_documents(cls, index_name, chunks):
        await es_client.index_documents(index_name, chunks)

    @classmethod
    async def mix_retrival_documents(cls, query_list, knowledges_id, search_field="summary"):

        if app_settings.rag.enable_elasticsearch:
            es_documents, milvus_documents = await MixRetrival.mix_retrival_documents(query_list, knowledges_id, search_field)
            # 先对ES和Milvus结果分别排序
            es_documents.sort(key=lambda x: x.score, reverse=True)
            milvus_documents.sort(key=lambda x: x.score, reverse=True)
            all_documents = es_documents + milvus_documents
        else:
            all_documents = await MixRetrival.retrival_milvus_documents(query_list, knowledges_id, search_field)

        # 合并并去重，保留分数更高的文档
        documents = []
        seen_chunk_ids = set()

        # 按分数从高到低排序
        all_documents.sort(key=lambda x: x.score, reverse=True)
        
        # 去重，保留分数最高的
        for doc in all_documents:
            if doc.chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(doc.chunk_id)
                documents.append(doc)
                if len(documents) >= 10:  # 限制返回10个文档
                    break
        
        return documents

    @classmethod
    async def rag_query_summary(cls, query, knowledges_id, min_score: Optional[float]=None,
                                top_k: Optional[int]=None, needs_query_rewrite: bool=True):
        if min_score is None:
            min_score = app_settings.rag.retrival.get('min_score')
        if top_k is None:
            top_k = app_settings.rag.retrival.get('top_k')

        # 查询重写
        if needs_query_rewrite:
            rewritten_queries = await cls.query_rewrite(query)
        else:
            rewritten_queries = [query]

        # 文档检索
        retrieved_documents = await cls.mix_retrival_documents(rewritten_queries, knowledges_id, "summary")

        # 准备重排序的文档内容
        documents_to_rerank = [doc.content for doc in retrieved_documents]

        # 文档重排序
        reranked_docs = await Reranker.rerank_documents(query, documents_to_rerank)

        # 过滤结果
        filtered_results = []
        # 确保top_k不为None
        actual_top_k = top_k if top_k is not None else 0
        if len(reranked_docs) >= actual_top_k:
            for doc in reranked_docs[:actual_top_k]:
                if min_score is not None and doc.score >= min_score:
                    filtered_results.append(doc)
            # 拼接最终结果
            final_result = "\n".join(result.content for result in filtered_results)
            return final_result
        else:
            logger.info(f"Recall for summary Field numbers < top k, Start recall use content Field")
            return await cls.retrieve_ranked_documents(query, knowledges_id, knowledges_id)


    @classmethod
    async def retrieve_ranked_documents(cls, query, collection_names, index_names=None, min_score: Optional[float]=None,
                        top_k: Optional[int]=None, needs_query_rewrite: bool=True):
        """
        处理 RAG 流程：查询重写、文档检索、重排序、结果过滤和拼接。

        Args:
            query (str): 用户查询。
            collection_names (list[str]): 向量知识库 集合ID。
            index_names (list[str]): ES关键词库 集合ID。
            min_score (float): 文档最低分数阈值，默认为配置中的值。
            top_k (int): 召回文档的个数。
            needs_query_rewrite (bool): 是否需要开启Query重写，默认开启

        Returns:
            str: 拼接后的最终结果。
            """
        if min_score is None:
            min_score = app_settings.rag.retrival.get('min_score')
        if top_k is None:
            top_k = app_settings.rag.retrival.get('top_k')

        # 查询重写
        if needs_query_rewrite:
            rewritten_queries = await cls.query_rewrite(query)
        else:
            rewritten_queries = [query]

        # 文档检索
        retrieved_documents = await cls.mix_retrival_documents(rewritten_queries, collection_names, "content")

        # 准备重排序的文档内容
        documents_to_rerank = [doc.content for doc in retrieved_documents]

        # 文档重排序
        reranked_docs = await Reranker.rerank_documents(query, documents_to_rerank)

        # 过滤结果
        filtered_results = []
        # 确保top_k不为None
        actual_top_k = top_k if top_k is not None else 0
        docs_to_process = reranked_docs if len(reranked_docs) <= actual_top_k else reranked_docs[:actual_top_k]
        for doc in docs_to_process:
            if min_score is not None and doc.score >= min_score:
                filtered_results.append(doc)

        # 处理空结果
        if not filtered_results:
            return "No relevant documents found."

        # 拼接最终结果
        final_result = "\n".join(result.content for result in filtered_results)
        return final_result

    @classmethod
    async def delete_documents_es_milvus(cls, file_id, knowledge_id):
        if app_settings.rag.enable_elasticsearch:
            await es_client.delete_documents(file_id, knowledge_id)
        await milvus_client.delete_by_file_id(file_id, knowledge_id)
