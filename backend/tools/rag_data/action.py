# from services.rag import vector_store
# from services.rag import document_reranker
#
# def exec_rag(query: str, top_k: int = 6):
#     retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
#
#     retrieved_docs = retriever.invoke(query)
#
#     docs = document_reranker(query=query,
#                              passages=retrieved_docs,
#                              vector_store=vector_store,
#                              top_k=top_k)
#     return docs
