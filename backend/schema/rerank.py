from pydantic import BaseModel

class RerankResultModel:
    def __init__(self, query, content, score, index):
        self.query = query
        self.content = content
        self.score = score
        self.index = index

    def to_dict(self):
        return {
            "query": self.query,
            "content": self.content,
            "score": self.score,
            "index": self.index
        }
