import os

import requests
import logging
from mcp.server import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("MCP-Weather")

weather_api_key = os.getenv("weather_api_key")
weather_endpoint = os.getenv("weather_endpoint")

@mcp.tool()
def get_weather(location: str):
    """帮助用户想要查询的天气

    Args:
        location: 查询天气的位置
    """
    params = {
        'key': weather_api_key,
        'city': location,
        'extensions': 'all'
    }

    try:
        res = requests.get(url=weather_endpoint, params=params, timeout=5)  # 预报天气
        result = res.json()
        city = result.get('forecasts')[0].get("city")  # 获取城市
        message_result = []
        data = result.get('forecasts')[0].get("casts")
        for item in data:
            date = item.get('date')  # 获取日期
            day_temp = item.get('daytemp')  # 白天温度
            night_temp = item.get('nighttemp')  # 晚上温度
            day_weather = item.get('dayweather')  # 白天天气现象
            night_weather = item.get('nightweather')  # 晚上天气现象
            weather_message = MESSAGE_PROMPT.format(date, day_temp, night_temp, day_weather, night_weather)

            message_result.append(weather_message)

        final_result = WEATHER_PROMPT.format(city, message_result[0], message_result[1:])
        return final_result
    except Exception as err:
        logging.error(f'call weather tool appear Err: {err}')
        return str(err)

WEATHER_PROMPT = """
以下是 {} 地区的天气情况：
今天的实时天气为:
{}

预报天气为:
{}

"""

MESSAGE_PROMPT = "日期: {}, 白天温度:{}, 晚上温度: {}, 白天气象:{}, 晚上气象:{}"

if __name__ == "__main__":
    mcp.run(transport="stdio")