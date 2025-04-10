from loguru import logger
from settings import app_settings
from services.rag.embedding import get_embedding
from schema.search import SearchModel
from pymilvus import connections, Collection, utility, FieldSchema, DataType, CollectionSchema


class MilvusClient:
    def __init__(self, **kwargs):
        self.milvus_host = app_settings.milvus.get('host')
        self.milvus_port = app_settings.milvus.get('port')


        connections.connect("default", host=self.milvus_host, port=self.milvus_port)
        self.collections = self._get_collection()

    def _collection_exists(self, collection_name):
        """检查集合是否存在"""
        return utility.has_collection(collection_name)

    async def create_collection(self, collection_name):
        if not self._collection_exists(collection_name):
            """创建 Milvus 集合"""
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
                FieldSchema(name="summary", dtype=DataType.VARCHAR, max_lenth=512),
                FieldSchema(name="embedding_summary", dtype=DataType.FLOAT_VECTOR, dim=768),
                FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=128),
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
            # 为embedding_summary字段创建索引
            collection.create_index("embedding_summary", index_params)
            self.collections[collection_name] = collection
            logger.info(f'Successful create milvus collection name: {collection_name}')

    async def search(self, query, collection_name, top_k=10):
        """
            在指定集合中搜索相似数据
            :param collection_name: 要搜索的集合名称
            :param query: 查询文本
            :param top_k: 返回的结果数量
            :return: 搜索结果
        """
        # 获取集合实例
        collection = self.collections.get(collection_name)

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
            anns_field="embedding",  # 向量字段名
            param=search_params,
            limit=top_k,
            output_fields=["content", "chunk_id", "summary", "file_id", "file_name", "knowledge_id", "update_time"]  # 返回的字段
        )

        # 格式化结果
        documents = []
        for hit in results[0]:
            documents.append(
                SearchModel(
                    content=hit.entity.get("content", ""),  # 获取内容
                    chunk_id=hit.entity.get("chunk_id", ""),  # 获取块 ID
                    file_id=hit.entity.get("file_id", ""),  # 获取文件 ID
                    file_name=hit.entity.get("file_name", ""),  # 获取文件名
                    knowledge_id=hit.entity.get("knowledge_id", ""),  # 获取知识库 ID
                    update_time=hit.entity.get("update_time", ""),  # 获取更新时间
                    summary=hit.entity.get("summary", ""),
                    score=hit.distance))

        return documents

    async def search_summary(self, query, collection_name, top_k=10):
        """
        在指定集合中搜索相似数据
        :param collection_name: 要搜索的集合名称
        :param query: 查询文本
        :param top_k: 返回的结果数量
        :return: 搜索结果
        """
        # 获取集合实例
        collection = self.collections.get(collection_name)

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
            anns_field="embedding_summary",  # 向量字段名
            param=search_params,
            limit=top_k,
            output_fields=["content", "chunk_id", "summary", "file_id", "file_name", "knowledge_id", "update_time"]  # 返回的字段
        )

        # 格式化结果
        documents = []
        for hit in results[0]:
            documents.append(
                SearchModel(
                    content=hit.entity.get("content", ""),  # 获取内容
                    chunk_id=hit.entity.get("chunk_id", ""),  # 获取块 ID
                    file_id=hit.entity.get("file_id", ""),  # 获取文件 ID
                    file_name=hit.entity.get("file_name", ""),  # 获取文件名
                    knowledge_id=hit.entity.get("knowledge_id", ""),  # 获取知识库 ID
                    update_time=hit.entity.get("update_time", ""),  # 获取更新时间
                    summary=hit.entity.get("summary", ""),
                    score=hit.distance))

        return documents

    async def delete_by_file_id(self, file_id, collection_name):
        # 获取集合实例
        collection = self.collections.get(collection_name)
        try:
            # 构造正确的查询表达式（假设 file_id 是字符串类型）
            query_expr = f'file_id == "{file_id}"'

            # 查询符合条件的文档
            results = collection.query(query_expr, output_fields=["id"])
            delete_ids = [result['id'] for result in results]

            # 如果找到匹配的文档，执行删除操作
            if delete_ids:
                # 将列表转换为 Milvus 支持的字符串格式
                delete_expr = f"id in {delete_ids}"
                collection.delete(delete_expr)
                logger.info(f'Successfully deleted {len(delete_ids)} documents for file_id: {file_id}')
            else:
                logger.info(f'No documents found for file_id: {file_id}')
        except ValueError as e:
            logger.error(f'ValueError occurred while deleting file_id:{file_id}: {e}')
        except Exception as e:
            logger.error(f'Unexpected error occurred while deleting  file_id:{file_id}: {e}')


    async def insert(self, collection_name, chunks):
        """插入数据到当前集合"""
        if collection_name not in self.collections:
            await self.create_collection(collection_name)
            # raise ValueError("Collection is not set. Use set_collection() first.")
        content_list, summary_list, chunk_id_list, file_id_list, file_name_list, update_time_list, knowledge_id_list = [], [], [], [], [], [], []

        for chunk in chunks:
            content_list.append(chunk.content)
            summary_list.append(chunk.summary)
            chunk_id_list.append(chunk.chunk_id)
            file_id_list.append(chunk.file_id)
            file_name_list.append(chunk.file_name)
            update_time_list.append(chunk.update_time)
            knowledge_id_list.append(chunk.knowledge_id)


        embedding_list = await get_embedding(content_list)
        embedding_summary_list = await get_embedding(summary_list)

        # 组织数据
        data = [
            chunk_id_list,  # chunk_id
            content_list,  # content
            embedding_list,  # embedding
            summary_list,   # summary
            embedding_summary_list, # embedding summary
            file_id_list,  # file_id
            file_name_list,  # file_name
            knowledge_id_list,  # knowledge_id
            update_time_list  # update_time
        ]

        # 获取collection_name 的对象
        collection = self.collections.get(collection_name)
        collection.insert(data)
        collection.flush()

    async def delete_collection(self, collection_name):
        """
        删除一个集合
        :param collection_name: 要删除的集合名称
        """
        if collection_name not in self.collections:
            print(f"集合 '{collection_name}' 不存在，无法删除。")
            return

        # 删除集合
        Collection(collection_name).drop()
        print(f"集合 '{collection_name}' 删除成功。")

        # 更新集合列表
        self.collections.pop(collection_name)

    # 获取单机Host中所有的集合
    def _get_collection(self):
        collections = {}
        for collection in Collection.list_collections():
            collections[collection] = Collection(collection)
        return collections

    def close(self):
        connections.disconnect("default")

client = MilvusClient()