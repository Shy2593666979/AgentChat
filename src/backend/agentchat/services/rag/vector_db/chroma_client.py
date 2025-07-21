from loguru import logger
from agentchat.settings import app_settings
from agentchat.services.rag.embedding import get_embedding
from agentchat.schema.search import SearchModel
from typing import Dict, Optional, List
import chromadb

"""
向量库的备选方案，下列代码未经测试
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
            self.client = chromadb.Client()
            logger.info(f"Successfully connected to Chroma")
        except Exception as e:
            logger.error(f"Failed to connect to Chroma: {e}")
            raise

    def _initialize_collections(self):
        """移除此方法，改为懒加载模式"""
        pass

    def _get_collection_safe(self, collection_name: str) -> Optional[chromadb.Collection]:
        """安全地获取集合"""
        try:
            if collection_name not in self.collections:
                try:
                    collection = self.client.get_collection(collection_name)
                    self.collections[collection_name] = collection
                    logger.debug(f"Collection '{collection_name}' retrieved and added to cache")
                except Exception as e:
                    logger.error(f"Collection '{collection_name}' does not exist: {e}")
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
            logger.info(f"Collection '{collection_name}' already exists")
            return

        try:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "l2"}  # 使用 L2 距离度量
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
            query_embedding = await get_embedding(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"]
            )

            documents = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                documents.append(
                    SearchModel(
                        content=results['documents'][0][i],
                        chunk_id=metadata.get("chunk_id", ""),
                        file_id=metadata.get("file_id", ""),
                        file_name=metadata.get("file_name", ""),
                        knowledge_id=metadata.get("knowledge_id", ""),
                        update_time=metadata.get("update_time", ""),
                        summary=metadata.get("summary", ""),
                        score=results['distances'][0][i]
                    )
                )
            return documents
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
            query_embedding = await get_embedding(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"],
                where={"is_summary": True}  # 假设摘要有特定标记
            )

            documents = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                documents.append(
                    SearchModel(
                        content=results['documents'][0][i],
                        chunk_id=metadata.get("chunk_id", ""),
                        file_id=metadata.get("file_id", ""),
                        file_name=metadata.get("file_name", ""),
                        knowledge_id=metadata.get("knowledge_id", ""),
                        update_time=metadata.get("update_time", ""),
                        summary=metadata.get("summary", ""),
                        score=results['distances'][0][i]
                    )
                )
            return documents
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
            collection.delete(where={"file_id": file_id})
            logger.info(f"Successfully deleted documents for file_id: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file_id {file_id} from collection {collection_name}: {e}")
            return False

    async def insert(self, collection_name: str, chunks) -> bool:
        """插入数据到指定集合"""
        if collection_name not in self.collections:
            await self.create_collection(collection_name)

        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot insert into collection '{collection_name}' - collection not available")
            return False

        try:
            ids, documents, embeddings, metadatas = [], [], [], []
            for chunk in chunks:
                ids.append(chunk.chunk_id)
                documents.append(chunk.content)
                metadatas.append({
                    "chunk_id": chunk.chunk_id,
                    "file_id": chunk.file_id,
                    "file_name": chunk.file_name,
                    "knowledge_id": chunk.knowledge_id,
                    "update_time": chunk.update_time,
                    "summary": chunk.summary,
                    "is_summary": False
                })
                # 额外添加摘要的嵌入
                ids.append(f"{chunk.chunk_id}_summary")
                documents.append(chunk.summary)
                metadatas.append({
                    "chunk_id": chunk.chunk_id,
                    "file_id": chunk.file_id,
                    "file_name": chunk.file_name,
                    "knowledge_id": chunk.knowledge_id,
                    "update_time": chunk.update_time,
                    "summary": chunk.summary,
                    "is_summary": True
                })

            # 生成嵌入向量
            content_embeddings = await get_embedding(documents[::2])  # 内容嵌入
            summary_embeddings = await get_embedding(documents[1::2])  # 摘要嵌入
            embeddings = []
            for i in range(len(content_embeddings)):
                embeddings.append(content_embeddings[i])
                embeddings.append(summary_embeddings[i])

            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(f"Successfully inserted {len(chunks)} chunks into collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to insert data into collection '{collection_name}': {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        if collection_name not in self.collections:
            logger.warning(f"Collection '{collection_name}' not found in cache")
            return False

        try:
            self.client.delete_collection(collection_name)
            self.collections.pop(collection_name, None)
            logger.info(f"Collection '{collection_name}' deleted successfully")
            return True
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
            return [col.name for col in self.client.list_collections()]
        except Exception as e:
            logger.error(f"Failed to get collection list: {e}")
            return []

    def close(self):
        """关闭连接并清理资源"""
        try:
            self.collections.clear()
            logger.info("Chroma connection closed and all collections unloaded")
        except Exception as e:
            logger.error(f"Error closing Chroma connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
