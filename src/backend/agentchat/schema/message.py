from typing import Literal, Any


class Message:
    def __init__(self, content: Any, role: Literal["user", "system", "assistant"] = "system"):
        self.role = role
        self.content = content
        
    def to_str(self):
        """Return the string representation of the message"""
        return f"{self.role}: {self.content} \n"

    def to_json(self):
        return {"role": self.role, "content": self.content}
        