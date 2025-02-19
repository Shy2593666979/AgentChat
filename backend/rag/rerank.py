from FlagEmbedding import FlagReranker
from langchain_cohere.rerank import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from operator import itemgetter
from utils.helpers import check_or_create
from langchain_core.vectorstores import VectorStore
from settings import app_settings

def document_reranker(query: str, passages: list, vector_store: VectorStore, top_k: int):
    pass
    # if userConfig.RAG_RERANK_CHOOSE == 'default':
    #     check_or_create(userConfig.RAG_RERANK_DEFAULT_CACHE_DIR)
    #
    #     reranker = FlagReranker(model_name_or_path=userConfig.RAG_RERANK_DEFAULT_MODEL,
    #                             cache_dir=userConfig.RAG_RERANK_DEFAULT_CACHE_DIR)
    #
    #     scores = reranker.compute_score([[query, page] for page in passages])
    #
    #     if isinstance(scores, list):
    #         similarity_dict = {page: scores[i] for i, page in enumerate(passages)}
    #     else:
    #         similarity_dict = {page: scores for i, page in enumerate(passages)}
    #
    #     sorted_result = sorted(similarity_dict.items(), key=itemgetter(1), reverse=True)
    #
    #     result = {}
    #
    #     # 选取得分较高的top_k个数据
    #     for i in range(top_k):
    #         result[sorted_result[i][0]] = sorted_result[i][1]
    #
    #     return result
    # else:
    #     reranker = CohereRerank(model=userConfig.RAG_RERANK_COHERE_MODEL,
    #                             cohere_api_key=userConfig.RAG_RERANK_COHERE_API_KEY)
    #
    #     compression_retriever = ContextualCompressionRetriever(
    #         base_compressor=reranker,
    #         base_retriever=vector_store.as_retriever()
    #     )
    #     compressed_docs = compression_retriever.get_relevant_documents(query)
    #     return compressed_docs
