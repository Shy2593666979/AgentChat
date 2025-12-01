import pytz
from datetime import datetime, timedelta

def get_beijing_time():
    # 设置北京时区
    beijing_tz = pytz.timezone('Asia/Shanghai')

    # 获取当前的北京时区时间
    current_bj_time = datetime.now(beijing_tz)
    formatted_time = current_bj_time.strftime("%Y-%m-%d %H:%M")

    return formatted_time

def get_beijing_date_str():
    """获取当前北京时间，并返回格式为 'YYYY-m-d' 的字符串（如 2025-6-30）"""
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    return f"{now.year}-{now.month}-{now.day}"


def get_current_date():
    current_date = datetime.now()
    return current_date.strftime("%Y-%m-%d")


def get_current_and_future_dates(days=7):
    """
    计算当前日期和未来指定天数后的日期。

    :param days: 从当前日期起的天数，默认为7天。
    :return: 当前日期和未来日期的字符串（格式：YYYY-MM-DD）。

    # 使用示例
    # current_date, future_date = get_current_and_future_dates()
    # print("当前日期:", current_date)
    # print("7天后日期:", future_date)
    """
    current_date = datetime.now()
    future_date = current_date + timedelta(days=days)

    return current_date.strftime("%Y-%m-%d"), future_date.strftime("%Y-%m-%d")


