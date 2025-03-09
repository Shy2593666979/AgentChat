
class SearchModel:
    def __init__(self, chunk_id, content, score, file_id, file_name, update_time, knowledge_id, summary):
        self.chunk_id = chunk_id
        self.content = content
        self.summary = summary
        self.file_id = file_id
        self.score = score
        self.file_name = file_name
        self.update_time = update_time
        self.knowledge_id = knowledge_id

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "summary": self.summary,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "knowledge_id": self.knowledge_id,
            "update_time": self.update_time
        }