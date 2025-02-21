from services.rag.embedding import get_embedding
from pymilvus import connections, Collection, utility, FieldSchema, DataType, CollectionSchema


class MilvusClient:
    def __init__(self, **kwargs):
        self.milvus_host = kwargs.get('milvus_host')
        self.milvus_port = kwargs.get('milvus_port')


        connections.connect("default", host=self.milvus_host, port=self.milvus_port)

        self.collections = self._get_collection()

    def _collection_exists(self, collection_name):
        """检查集合是否存在"""
        return utility.has_collection(collection_name)

    def _create_collection(self, collection_name):
        if not self._collection_exists(collection_name):
            """创建 Milvus 集合"""
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
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
            self.collections[collection_name] = collection

    def search(self, collection_name, query, top_k=10):
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
        query_embedding = get_embedding(query)

        # 定义搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }

        # 执行搜索
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",  # 向量字段名
            param=search_params,
            limit=top_k,
            output_fields=["text"]  # 返回的字段
        )

        # 格式化结果
        return [(hit.entity.get("text"), hit.distance) for hit in results[0]]

    def insert(self, collection_name, text):
        """插入数据到当前集合"""
        if collection_name not in self.collections :
            raise Exception("Collection is not set. Use set_collection() first.")
        embedding = get_embedding(text)
        data = [[text], [embedding]]

        # 获取collection_name 的对象
        collection = self.collections.get(collection_name)
        collection.insert(data)
        collection.flush()

    def delete_collection(self, collection_name):
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