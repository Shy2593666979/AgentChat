import asyncio
from loguru import logger
import chromadb
from chromadb.config import Settings
from typing import Dict, Optional, List
import uuid
import numpy as np


# Mock SearchModel for the examples
class SearchModel:
    def __init__(self, content, chunk_id, file_id, file_name, knowledge_id, update_time, summary, score):
        self.content = content
        self.chunk_id = chunk_id
        self.file_id = file_id
        self.file_name = file_name
        self.knowledge_id = knowledge_id
        self.update_time = update_time
        self.summary = summary
        self.score = score


# Mock get_embedding function
async def get_embedding(texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = [np.random.rand(1024).tolist() for _ in texts]
    logger.debug(f"Generated embeddings: {embeddings}")
    return embeddings


# ChromaClient class (same as provided earlier, included for completeness)
class ChromaClient:
    def __init__(self, **kwargs):
        self.chroma_host = kwargs.get('host', 'localhost')
        self.chroma_port = kwargs.get('port', '8000')
        self.collections: Dict[str, chromadb.Collection] = {}
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = chromadb.Client()
            logger.info(f"Successfully connected to Chroma at {self.chroma_host}:{self.chroma_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Chroma: {e}")
            raise

    def _get_collection_safe(self, collection_name: str) -> Optional[chromadb.Collection]:
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
        try:
            self.client.get_collection(collection_name)
            return True
        except Exception:
            return False

    async def create_collection(self, collection_name: str):
        if self._collection_exists(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            return
        try:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "l2"}
            )
            self.collections[collection_name] = collection
            logger.info(f"Successfully created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise

    async def search(self, query: str, collection_name: str, top_k: int = 10) -> List[SearchModel]:
        collection = self._get_collection_safe(collection_name)
        if not collection:
            logger.error(f"Cannot search in collection '{collection_name}' - collection not available")
            return []
        try:
            query_embedding = await get_embedding(query)
            # 确保 query_embedding 是二维列表
            if isinstance(query_embedding, list) and len(query_embedding) > 0 and isinstance(query_embedding[0], list) and isinstance(query_embedding[0][0], list):
                query_embedding = query_embedding[0]  # 展平一层
            logger.debug(f"Query embedding shape: {len(query_embedding)} vectors")
            results = collection.query(
                query_embeddings=query_embedding,
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
                where={"is_summary": True}
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
            content_embeddings = await get_embedding(documents[::2])
            summary_embeddings = await get_embedding(documents[1::2])
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
        return list(self.collections.keys())

    def get_all_collections(self) -> List[str]:
        try:
            return [col.name for col in self.client.list_collections()]
        except Exception as e:
            logger.error(f"Failed to get collection list: {e}")
            return []

    def close(self):
        try:
            self.collections.clear()
            logger.info("Chroma connection closed and all collections unloaded")
        except Exception as e:
            logger.error(f"Error closing Chroma connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example 1: Create a Collection
async def example_create_collection():
    client = ChromaClient()
    collection_name = "test_collection"
    await client.create_collection(collection_name)
    print(f"Created collection: {collection_name}")
    client.close()


# Example 2: Insert Data
class MockChunk:
    def __init__(self, content, summary, chunk_id, file_id, file_name, knowledge_id, update_time):
        self.content = content
        self.summary = summary
        self.chunk_id = chunk_id
        self.file_id = file_id
        self.file_name = file_name
        self.knowledge_id = knowledge_id
        self.update_time = update_time


async def example_insert_data():
    client = ChromaClient()
    collection_name = "test_collection"

    # Create sample chunks
    chunks = [
        MockChunk(
            content="This is a sample document about AI.",
            summary="AI document summary.",
            chunk_id=str(uuid.uuid4()),
            file_id="file_001",
            file_name="ai_doc.txt",
            knowledge_id="kb_001",
            update_time="2025-07-21"
        ),
        MockChunk(
            content="Machine learning is a subset of AI.",
            summary="ML is part of AI.",
            chunk_id=str(uuid.uuid4()),
            file_id="file_002",
            file_name="ml_doc.txt",
            knowledge_id="kb_001",
            update_time="2025-07-21"
        )
    ]

    success = await client.insert(collection_name, chunks)
    print(f"Insert data: {'Success' if success else 'Failed'}")
    client.close()


# Example 3: Search Data
async def example_search_data():
    client = ChromaClient()
    collection_name = "test_collection"
    query = "Artificial Intelligence"
    results = await client.search(query, collection_name, top_k=5)

    print("Search Results:")
    for result in results:
        print(f"Content: {result.content}, Score: {result.score}, File: {result.file_name}")
    client.close()


# Example 4: Delete Data by File ID
async def example_delete_by_file_id():
    client = ChromaClient()
    collection_name = "test_collection"
    file_id = "file_001"
    success = await client.delete_by_file_id(file_id, collection_name)
    print(f"Delete file_id {file_id}: {'Success' if success else 'Failed'}")
    client.close()


# Example 5: Delete Collection
async def example_delete_collection():
    client = ChromaClient()
    collection_name = "test_collection"
    success = await client.delete_collection(collection_name)
    print(f"Delete collection {collection_name}: {'Success' if success else 'Failed'}")
    client.close()


# Run all examples sequentially
async def run_examples():
    print("Running Example 1: Create Collection")
    await example_create_collection()
    print("\nRunning Example 2: Insert Data")
    await example_insert_data()
    print("\nRunning Example 3: Search Data")
    await example_search_data()
    print("\nRunning Example 4: Delete by File ID")
    await example_delete_by_file_id()
    print("\nRunning Example 5: Delete Collection")
    await example_delete_collection()


if __name__ == "__main__":
    asyncio.run(run_examples())
