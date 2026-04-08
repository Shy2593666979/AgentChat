import uuid
import tiktoken
from datetime import datetime, timedelta, timezone

def get_now_time() -> datetime:
    # 东八区时区 = UTC+8
    beijing_tz = timezone(timedelta(hours=8), name="Asia/Shanghai")
    return datetime.now(beijing_tz)

def generate_uuid() -> str:
    return str(uuid.uuid4())

def count_tokens_usage(text: str, model: str=None):
    """
    计算普通文本的 token 数量, 使用国产模型只能计算大概token使用量，±10%
    """
    if model:
        enc = tiktoken.encoding_for_model(model)
    else:
        enc = tiktoken.get_encoding("cl100k_base")

    return len(enc.encode(text))