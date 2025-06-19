from loguru import logger

import requests
from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from agentchat.settings import app_settings
from agentchat.prompts.tool_prompt import WEATHER_PROMPT, MESSAGE_PROMPT


class WeatherInput(BaseModel):
    location: str = Field(description='输入输入想要查询的位置')


class WeatherTool(BaseTool):
    name: str = 'weather'
    description: str = '帮助用户想要查询的天气'
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, location: str):
            return get_weather(location)


def get_weather(location: str):
    """帮助用户想要查询的天气"""
    params = {
        'key': app_settings.tool_weather.get('api_key'),
        'city': location,
        'extensions': 'all'
    }

    try:
        res = requests.get(url=app_settings.tool_weather.get('endpoint'), params=params, timeout=5)  # 预报天气
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
        logger.error(f'call weather tool appear Err: {err}')
        return str(err)


