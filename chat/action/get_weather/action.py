import requests
from config.tool_config import WEATHER_URL, WEATHER_API_KEY
from chat.prompt.weather_prompt import WEATHER_PROMPT, MESSAGE_PROMPT

def get_weather_action(location: str):
    params = {
        'key': WEATHER_API_KEY,
        'city': location,
        'extensions': 'all'
    }

    res = requests.get(url=WEATHER_URL, params=params) # 预报天气

    result = res.json()


    city = result.get('forecasts')[0].get("city")  # 获取城市
    message_result = []
    data = result.get('forecasts')[0].get("casts")[0]
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

