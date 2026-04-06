import uuid
from datetime import datetime, timedelta, timezone

def get_now_time() -> datetime:
    # 东八区时区 = UTC+8
    beijing_tz = timezone(timedelta(hours=8), name="Asia/Shanghai")
    return datetime.now(beijing_tz)


def generate_uuid() -> str:
    return str(uuid.uuid4())