from loguru import logger
from agentchat.settings import app_settings
from agentchat.services.rag.embedding import get_embedding
from agentchat.schema.search import SearchModel
from pymilvus import connections, Collection, utility, FieldSchema, DataType, CollectionSchema
from typing import Dict, Optional, List


class MilvusClient:
    def __init__(self, **kwargs):
        self.milvus_host = app_settings.rag.vector_db.get('host')
        self.milvus_port = app_settings.rag.vector_db.get('port')
        self.collections: Dict[str, Collection] = {}
        self.loaded_collections: set = set()  # 跟踪已加载的集合

        # 连接管理
        self._connect()

    def _connect(self):
        """建立 Milvus 连接"""
        try:
            connections.connect("default", host=self.milvus_host, port=self.milvus_port)
            logger.info(f"Successfully connected to Milvus at {self.milvus_host}:{self.milvus_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _initialize_collections(self):
        """移除此方法，改为懒加载模式"""
        pass

    def _ensure_collection_loaded(self, collection: Collection) -> bool:
        """确保集合被加载到内存中（懒加载）"""
        collection_name = collection.name

        # 如果已经加载过，直接返回
        if collection_name in self.loaded_collections:
            return True

        try:
            # 尝试加载集合
            collection.load()
            self.loaded_collections.add(collection_name)
            logger.info(f"Collection '{collection_name}' loaded successfully")
            return True
        except Exception as e:
            # 如果加载失败，可能是因为集合已经加载或其他原因
            try:
                # 尝试通过简单查询来验证集合是否可用
                self.loaded_collections.add(collection_name)
                logger.info(f"Collection '{collection_name}' is already loaded")
                return True
            except Exception as inner_e:
                logger.error(f"Failed to load collection '{collection_name}': {e}, verification failed: {inner_e}")
                return False

    def _get_collection_safe(self, collection_name: str) -> Optional[Collection]:
        """安全地获取集合，按需加载（懒加载）"""
        try:
            # 如果集合不在缓存中，先检查是否存在
            if collection_name not in self.collections:
                if not self._collection_exists(collection_name):
                    logger.error(f"Collection '{collection_name}' does not exist")
                    return None

                # 创建集合对象但不立即加载
                collection = Collection(collection_name)
                self.collections[collection_name] = collection
                logger.debug(f"Collection '{collection_name}' added to cache")

            collection = self.collections[collection_name]

            # 懒加载：只有在实际使用时才加载到内存
            if not self._ensure_collection_loaded(collection):
                logger.warning(f"Collection '{collection_name}' may not be fully loaded, but will try to proceed")

            return collection

        except Exception as e:
            logger.error(f"Error getting collection '{collection_name}': {e}")
            return None

    def _collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return utility.has_collection(collection_name)

    async def create_collection(self, collection_name: str):
        """创建 Milvus 集合（如果不存在）"""
        if self._collection_exists(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            return

        try:
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="embedding_summary", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="knowledge_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="update_time", dtype=DataType.VARCHAR, max_length=128),
            ]

            schema = CollectionSchema(fields, description=f"RAG Collection: {collection_name}")
            collection = Collection(collection_name, schema)

            # 创建索引
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            collection.create_index("embedding_summary", index_params)

            # 加载集合
            collection.load()

            self.collections[collection_name] = collection
            logger.info(f'Successfully created and loaded collection: {collection_name}')

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
            # 生成查询向量
            query_embedding = await get_embedding(query)

            # 定义搜索参数
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 16}
            }

            # 执行搜索
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["content", "chunk_id", "summary", "file_id", "file_name", "knowledge_id", "update_time"]
            )
    
            # 格式化结果
            documents = []
            for hit in results[0]:
                documents.append(
                    SearchModel(
                        content=hit.entity.content,
                        chunk_id=hit.entity.chunk_id,
                        file_id=hit.entity.file_id,
                        file_name=hit.entity.file_name,
                        knowledge_id=hit.entity.knowledge_id,
                        update_time=hit.entity.update_time,
                        summary=hit.entity.summary,
                        score=hit.distance
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
            # 生成查询向量
            query_embedding = await get_embedding(query)

            # 定义搜索参数
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 16}
            }

            # 执行搜索
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding_summary",
                param=search_params,
                limit=top_k,
                output_fields=["content", "chunk_id", "summary", "file_id", "file_name", "knowledge_id", "update_time"]
            )

            # 格式化结果
            documents = []
            for hit in results[0]:
                documents.append(
                    SearchModel(
                        content=hit.entity.get("content", ""),
                        chunk_id=hit.entity.get("chunk_id", ""),
                        file_id=hit.entity.get("file_id", ""),
                        file_name=hit.entity.get("file_name", ""),
                        knowledge_id=hit.entity.get("knowledge_id", ""),
                        update_time=hit.entity.get("update_time", ""),
                        summary=hit.entity.get("summary", ""),
                        score=hit.distance
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
            # 构造查询表达式
            query_expr = f'file_id == "{file_id}"'

            # 查询符合条件的文档
            results = collection.query(query_expr, output_fields=["id"])
            delete_ids = [result['id'] for result in results]

            # 如果找到匹配的文档，执行删除操作
            if delete_ids:
                delete_expr = f"id in {delete_ids}"
                collection.delete(delete_expr)
                collection.flush()  # 确保删除操作立即生效
                logger.info(f'Successfully deleted {len(delete_ids)} documents for file_id: {file_id}')
                return True
            else:
                logger.info(f'No documents found for file_id: {file_id}')
                return True

        except Exception as e:
            logger.error(f'Error deleting file_id {file_id} from collection {collection_name}: {e}')
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
            # 准备数据
            content_list, summary_list, chunk_id_list = [], [], []
            file_id_list, file_name_list, update_time_list, knowledge_id_list = [], [], [], []

            for chunk in chunks:
                content_list.append(chunk.content)
                summary_list.append(chunk.summary)
                chunk_id_list.append(chunk.chunk_id)
                file_id_list.append(chunk.file_id)
                file_name_list.append(chunk.file_name)
                update_time_list.append(chunk.update_time)
                knowledge_id_list.append(chunk.knowledge_id)

            # 生成嵌入向量
            embedding_list = await get_embedding(content_list)
            embedding_summary_list = await get_embedding(summary_list)

            # 组织数据
            data = [
                chunk_id_list,
                content_list,
                embedding_list,
                summary_list,
                embedding_summary_list,
                file_id_list,
                file_name_list,
                knowledge_id_list,
                update_time_list
            ]

            # 插入数据
            collection.insert(data)
            collection.flush()

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
            # 删除集合
            Collection(collection_name).drop()
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
                collection = self.collections[collection_name]
                collection.release()
                self.loaded_collections.discard(collection_name)
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
        return list(self.loaded_collections)

    def get_all_collections(self) -> List[str]:
        """获取所有可用集合列表（不加载）"""
        try:
            return utility.list_collections()
        except Exception as e:
            logger.error(f"Failed to get collection list: {e}")
            return []

    def close(self):
        """关闭连接并清理资源"""
        try:
            # 卸载所有已加载的集合
            for collection_name in list(self.loaded_collections):
                self.unload_collection(collection_name)

            connections.disconnect("default")
            logger.info("Milvus connection closed and all collections unloaded")
        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

