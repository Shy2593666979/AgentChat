from datetime import datetime
from zoneinfo import ZoneInfo

# 根据一个时间字符串转成时间戳
def convert_timestamp(current_time):

    dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M")

    # 添加北京时间时区
    beijing_time = dt.replace(tzinfo=ZoneInfo("Asia/Shanghai"))

    timestamp = int(beijing_time.timestamp())
    return str(timestamp)