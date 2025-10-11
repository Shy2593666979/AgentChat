from loguru import logger
from agentchat.settings import app_settings
from agentchat.services.rag.embedding import get_embedding
from agentchat.schema.search import SearchModel
from typing import Dict, Optional, List
import chromadb
import asyncio

"""
修复后的向量库Chroma客户端
"""


class ChromaClient:
    def __init__(self, **kwargs):
        self.collections: Dict[str, chromadb.Collection] = {}
        self.client = None
        # 连接管理
        self._connect()

    def _connect(self):
        """建立 Chroma 连接"""
        try:
            # 使用持久化客户端，避免内存丢失
            self.client = chromadb.PersistentClient(path="./vector_db")
            logger.info("Successfully connected to Chroma")
        except Exception as e:
            logger.error(f"Failed to connect to Chroma: {e}")
            raise

    def _get_collection_safe(self, collection_name: str) -> Optional[chromadb.Collection]:
        """安全地获取集合"""
        try:
            if collection_name not in self.collections:
                try:
                    collection = self.client.get_collection(collection_name)
                    self.collections[collection_name] = collection
                    logger.debug(f"Collection '{collection_name}' retrieved and added to cache")
                except Exception as e:
                    logger.debug(f"Collection '{collection_name}' does not exist: {e}")
                    return None
            return self.collections[collection_name]
        except Exception as e:
            logger.error(f"Error getting collection '{collection_name}': {e}")
            return None

    def _collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            self.client.get_collection(collection_name)
            return True
        except Exception:
            return False

    async def create_collection(self, collection_name: str):
        """创建 Chroma 集合（如果不存在）"""
        if self._collection_exists(collection_name):
            collection = self.client.get_collection(collection_name)
            self.collections[collection_name] = collection
            logger.info(f"Collection '{collection_name}' already exists")
            return

        try:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用cosine相似度
            )
            self.collections[collection_name] = collection
            logger.info(f"Successfully created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise

    async def search(self, query: str, collection_name: str, top_k: int = 10) -> List[SearchModel]:
        """在指定集合中搜索相似数据"""
        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot search in collection '{collection_name}' - collection not available")
            return []

        try:
            # 获取查询向量
            query_embeddings = await get_embedding([query])  # 确保传入列表
            if not query_embeddings or len(query_embeddings) == 0:
                logger.error("Failed to generate query embedding")
                return []

            query_embedding = query_embeddings[0]

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, 100),  # 限制最大返回数量
                include=["metadatas", "documents", "distances"]
            )

            if not results['ids'] or len(results['ids']) == 0 or len(results['ids'][0]) == 0:
                logger.info(f"No results found in collection '{collection_name}'")
                return []

            documents = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i] or {}
                # 过滤掉摘要条目，只返回原始内容
                if metadata.get("is_summary", False):
                    continue

                documents.append(
                    SearchModel(
                        content=results['documents'][0][i] or "",
                        chunk_id=metadata.get("chunk_id", ""),
                        file_id=metadata.get("file_id", ""),
                        file_name=metadata.get("file_name", ""),
                        knowledge_id=metadata.get("knowledge_id", ""),
                        update_time=metadata.get("update_time", ""),
                        summary=metadata.get("summary", ""),
                        score=1.0 - results['distances'][0][i]  # 转换为相似度分数
                    )
                )
            return documents[:top_k]  # 确保返回正确数量
        except Exception as e:
            logger.error(f"Search failed in collection '{collection_name}': {e}")
            return []

    async def search_summary(self, query: str, collection_name: str, top_k: int = 10) -> List[SearchModel]:
        """在指定集合中搜索相似数据（基于摘要）"""
        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot search in collection '{collection_name}' - collection not available")
            return []

        try:
            query_embeddings = await get_embedding([query])
            if not query_embeddings or len(query_embeddings) == 0:
                logger.error("Failed to generate query embedding")
                return []

            query_embedding = query_embeddings[0]

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k * 2, 100),  # 查询更多结果以便过滤
                include=["metadatas", "documents", "distances"],
                where={"is_summary": True}
            )

            if not results['ids'] or len(results['ids']) == 0 or len(results['ids'][0]) == 0:
                logger.info(f"No summary results found in collection '{collection_name}'")
                return []

            documents = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i] or {}
                documents.append(
                    SearchModel(
                        content=results['documents'][0][i] or "",
                        chunk_id=metadata.get("chunk_id", ""),
                        file_id=metadata.get("file_id", ""),
                        file_name=metadata.get("file_name", ""),
                        knowledge_id=metadata.get("knowledge_id", ""),
                        update_time=metadata.get("update_time", ""),
                        summary=metadata.get("summary", ""),
                        score=1.0 - results['distances'][0][i]
                    )
                )
            return documents[:top_k]
        except Exception as e:
            logger.error(f"Summary search failed in collection '{collection_name}': {e}")
            return []

    async def delete_by_file_id(self, file_id: str, collection_name: str) -> bool:
        """根据文件ID删除数据"""
        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot delete from collection '{collection_name}' - collection not available")
            return False

        try:
            # 先查询要删除的条目
            results = collection.get(where={"file_id": file_id})
            if not results['ids'] or len(results['ids']) == 0:
                logger.info(f"No documents found for file_id: {file_id}")
                return True

            # 删除找到的条目
            collection.delete(where={"file_id": file_id})
            logger.info(f"Successfully deleted {len(results['ids'])} documents for file_id: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file_id {file_id} from collection {collection_name}: {e}")
            return False

    async def insert(self, collection_name: str, chunks) -> bool:
        """插入数据到指定集合"""
        if not chunks:
            logger.warning("No chunks to insert")
            return True

        # 确保集合存在
        if collection_name not in self.collections:
            await self.create_collection(collection_name)

        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot insert into collection '{collection_name}' - collection not available")
            return False

        try:
            ids, documents, metadatas = [], [], []
            content_texts, summary_texts = [], []

            # 准备数据
            for chunk in chunks:
                # 内容条目
                ids.append(chunk.chunk_id)
                documents.append(chunk.content or "")
                content_texts.append(chunk.content or "")
                metadatas.append({
                    "chunk_id": chunk.chunk_id,
                    "file_id": chunk.file_id,
                    "file_name": chunk.file_name or "",
                    "knowledge_id": chunk.knowledge_id or "",
                    "update_time": chunk.update_time or "",
                    "summary": chunk.summary or "",
                    "is_summary": False
                })

                # 摘要条目（如果存在摘要）
                if chunk.summary and chunk.summary.strip():
                    ids.append(f"{chunk.chunk_id}_summary")
                    documents.append(chunk.summary)
                    summary_texts.append(chunk.summary)
                    metadatas.append({
                        "chunk_id": chunk.chunk_id,
                        "file_id": chunk.file_id,
                        "file_name": chunk.file_name or "",
                        "knowledge_id": chunk.knowledge_id or "",
                        "update_time": chunk.update_time or "",
                        "summary": chunk.summary,
                        "is_summary": True
                    })
                else:
                    summary_texts.append("")

            if not documents:
                logger.warning("No valid documents to insert")
                return True

            # 生成嵌入向量
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            all_embeddings = await get_embedding(documents)

            if not all_embeddings or len(all_embeddings) != len(documents):
                logger.error(
                    f"Embedding generation failed. Expected {len(documents)}, got {len(all_embeddings) if all_embeddings else 0}")
                return False

            # 分批插入以避免内存问题
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_documents = documents[i:i + batch_size]
                batch_embeddings = all_embeddings[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]

                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas
                )

                logger.debug(f"Inserted batch {i // batch_size + 1}: {len(batch_ids)} items")

            logger.info(f"Successfully inserted {len(chunks)} chunks into collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to insert data into collection '{collection_name}': {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if self._collection_exists(collection_name):
                self.client.delete_collection(collection_name)
                self.collections.pop(collection_name, None)
                logger.info(f"Collection '{collection_name}' deleted successfully")
                return True
            else:
                logger.warning(f"Collection '{collection_name}' does not exist")
                return False
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def unload_collection(self, collection_name: str) -> bool:
        """卸载集合以释放内存"""
        try:
            if collection_name in self.collections:
                self.collections.pop(collection_name)
                logger.info(f"Collection '{collection_name}' unloaded successfully")
                return True
            else:
                logger.warning(f"Collection '{collection_name}' not found in cache")
                return False
        except Exception as e:
            logger.error(f"Failed to unload collection '{collection_name}': {e}")
            return False

    def get_loaded_collections(self) -> List[str]:
        """获取当前已加载的集合列表"""
        return list(self.collections.keys())

    def get_all_collections(self) -> List[str]:
        """获取所有可用集合列表"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to get collection list: {e}")
            return []

    def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量"""
        collection = self._get_collection_safe(collection_name)
        if not collection:
            return 0
        try:
            result = collection.count()
            return result
        except Exception as e:
            logger.error(f"Failed to get count for collection '{collection_name}': {e}")
            return 0

    def close(self):
        """关闭连接并清理资源"""
        try:
            self.collections.clear()
            self.client = None
            logger.info("Chroma connection closed and all collections unloaded")
        except Exception as e:
            logger.error(f"Error closing Chroma connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()