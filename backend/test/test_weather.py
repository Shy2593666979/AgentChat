import requests
import sys
sys.path.append("..")


params = {
    'key': WEATHER_API_KEY,
    'city': '郑州',
    'extensions': 'all'
}

res = requests.get(url=WEATHER_URL, params=params)

tianqi = res.json()
print(tianqi)



city = tianqi.get('forecasts')[0].get("city") # 获取城市

date = tianqi.get('forecasts')[0].get("casts")[0].get('date') # 获取日期
dayweather = tianqi.get('forecasts')[0].get("casts")[0].get('dayweather') # 白天天气现象
nightweather = tianqi.get('forecasts')[0].get("casts")[0].get('nightweather') # 晚上天气现象
daytemp = tianqi.get('forecasts')[0].get("casts")[0].get('daytemp') # 白天温度
nighttemp = tianqi.get('forecasts')[0].get("casts")[0].get('nighttemp') # 晚上温度

