import re


def normalize_conversation_title(value: str) -> str:
    """清理标题的标点与空白，保证有效标题为 2—10 个字符。"""
    value = re.sub(r"<think>.*?</think>", "", value, flags=re.DOTALL).strip()
    value = next((line.strip() for line in value.splitlines() if line.strip()), "")
    value = re.sub(r"^(?:话题标题|会话标题|标题)\s*[:：]\s*", "", value)
    value = re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)[:10]
    return value if len(value) >= 2 else ""


def fallback_conversation_title(first_message: str) -> str:
    """模型生成失败时，保留第一条问题的短标题。"""
    return normalize_conversation_title(first_message) or "新会话"
