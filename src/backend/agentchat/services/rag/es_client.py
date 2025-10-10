import json
from typing import List
from elasticsearch import Elasticsearch

from agentchat.config.es_index import ESIndex
from agentchat.schema.chunk import ChunkModel
from agentchat.schema.search import SearchModel
from agentchat.settings import app_settings
from loguru import logger


class ESClient:
    def __init__(self):
        self.client = Elasticsearch(hosts=app_settings.rag.elasticsearch.get('hosts'))

    async def insert_documents(self, index_name, chunks: List[ChunkModel]):
        # 构造查询条件
        index_config = json.loads(ESIndex.index_config)

        if not self.client.indices.exists(index=index_name):

            try:
                self.client.indices.create(index=index_name, body=index_config)
                logger.info(f'index name: {index_name} 创建成功')
            except Exception as e:
                logger.error(f"index name {index_name} error: {e}")
                raise ValueError(f"index create error")
        try:
            for chunk in chunks:
                self.client.index(
                    index=index_name,
                    body=chunk.to_dict()
                )
                logger.info(f'chunk id: {chunk.chunk_id} 已存到索引中')
        except Exception as e:
            logger.error(f"索引增加数据失败：{e}")
        finally:
            await self.close()

    async def index_documents(self, index_name, chunks):
        await self.insert_documents(index_name, chunks)

    async def search_documents(self, query, index_name):
        index_search = json.loads(ESIndex.index_search_content.format(query=query))

        documents = []
        try:
            response = self.client.search(index=index_name, body=index_search)
            hits = response['hits']
            if not hits.get("max_score"):
                return documents
            for hit in response['hits']:
                documents.append(SearchModel(score=hit['_score'], chunk_id=hit['_source']['chunk_id'],
                                             update_time=hit['_source']['update_time'],
                                             content=hit['_source']['content'], file_name=hit['_source']['file_name'],
                                             summary=hit['_source']['summary'],
                                             file_id=hit['_source']['file_id'],
                                             knowledge_id=hit['_source']['knowledge_id']))
        except Exception as e:
            logger.error(f'Search documents error: {e}')
        finally:
            await self.close()
            return documents

    async def search_documents_summary(self, query, index_name):
        index_search = json.loads(ESIndex.index_search_summary.format(query=query))

        documents = []
        try:
            response = self.client.search(index=index_name, body=index_search)

            for hit in response['hits']:
                documents.append(SearchModel(score=hit['_score'], chunk_id=hit['_source']['chunk_id'],
                                             update_time=hit['_source']['update_time'],
                                             content=hit['_source']['content'], file_name=hit['_source']['file_name'],
                                             summary=hit['_source']['summary'],
                                             file_id=hit['_source']['file_id'],
                                             knowledge_id=hit['_source']['knowledge_id']))

        except Exception as e:
            logger.error(f'Search documents summary error: {e}')
        finally:
            await self.close()
            return documents

    async def delete_documents(self, file_id, index_name):
        try:
            # 构造查询条件
            delete_query = json.loads(ESIndex.index_delete.format(file_id=file_id))
            self.client.delete_by_query(index=index_name, body=delete_query)
            logger.info(f'Success delete documents in file id: {file_id}')
        except Exception as e:
            logger.error(f'Delete documents Error: {e}')

    async def close(self):
        pass


client = ESClient()

# ⭐Elasticsearch 在7.11版本之前不支持异步，因本地部署的7.0.0版本，所以使用的同步，如果ES版本较高，建议使用下面的异步代码⭐
# import json
# from typing import List
# from elasticsearch import AsyncElasticsearch
# from agentchat.schema.chunk import ChunkModel
# from agentchat.schema.search import SearchModel
# from agentchat.settings import app_settings
# from loguru import logger
#
# class AsyncESClient:
#     def __init__(self):
#         self.client = AsyncElasticsearch(hosts=app_settings.elasticsearch.get('hosts'))
#
#     async def insert_documents(self, index_name, chunks: List[ChunkModel]):
#         with open(app_settings.elasticsearch.get('index_config_path'), 'r') as f:
#             index_config = json.loads(f.read())
#
#         if not await self.client.indices.exists(index=index_name):
#
#             try:
#                 await self.client.indices.create(index=index_name, body=index_config)
#                 logger.info(f'index name: {index_name} 创建成功')
#             except Exception as e:
#                 logger.error(f"index name {index_name} error: {e}")
#                 raise ValueError(f"index create error")
#         try:
#             for chunk in chunks:
#                 await self.client.index(
#                     index=index_name,
#                     body=chunk.to_dict()
#                 )
#                 logger.info(f'chunk id: {chunk.chunk_id} 已存到索引中')
#         except Exception as e:
#             logger.error(f"索引增加数据失败：{e}")
#         finally:
#             await self.close()
#
#     async def index_documents(self, index_name, chunks):
#         await self.insert_documents(index_name, chunks)
#
#     async def search_documents(self, query, index_name):
#         with open(app_settings.elasticsearch.get('index_search_content_path'), 'r') as f:
#             content = f.read()
#             content = content.format(query=query)
#             index_search = json.loads(content)
#
#         try:
#             response = await self.client.search(index=index_name, body=index_search)
#
#             documents = []
#             for hit in response['hits']:
#                 documents.append(SearchModel(score=hit['_score'], chunk_id=hit['_source']['chunk_id'], update_time=hit['_source']['update_time'],
#                                              content=hit['_source']['content'], file_name=hit['_source']['file_name'], summary=hit['_source']['summary'],
#                                              file_id=hit['_source']['file_id'], knowledge_id=hit['_source']['knowledge_id']))
#
#         except Exception as e:
#             logger.error(f'Search documents error: {e}')
#         finally:
#             await self.close()
#
#     async def search_documents_summary(self, query, index_name):
#         with open(app_settings.elasticsearch.get('index_search_summary_path'), 'r') as f:
#             content = f.read()
#             content = content.format(query=query)
#             index_search = json.loads(content)
#
#         try:
#             response = await self.client.search(index=index_name, body=index_search)
#
#             documents = []
#             for hit in response['hits']:
#                 documents.append(SearchModel(score=hit['_score'], chunk_id=hit['_source']['chunk_id'], update_time=hit['_source']['update_time'],
#                                              content=hit['_source']['content'], file_name=hit['_source']['file_name'], summary=hit['_source']['summary'],
#                                              file_id=hit['_source']['file_id'], knowledge_id=hit['_source']['knowledge_id']))
#
#         except Exception as e:
#             logger.error(f'Search documents summary error: {e}')
#         finally:
#             await self.close()
#
#     async def delete_documents(self, file_id, index_name):
#         try:
#             # 构造查询条件
#             with open(app_settings.elasticsearch.get('index_delete_path'), 'r') as f:
#                 content = f.read()
#                 content = content.format(file_id=file_id)
#                 delete_query = json.loads(content)
#
#             await self.client.delete_by_query(index=index_name, body=delete_query)
#             logger.info(f'Success delete documents in file id: {file_id}')
#         except Exception as e:
#             logger.error(f'Delete documents in file id error: {e}')
#
#
#     async def close(self):
#         await self.client.close()
#
# client = AsyncESClient()
