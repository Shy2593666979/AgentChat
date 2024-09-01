import urllib.request
import urllib.parse
import ssl
import json
from config import user_config
from prompt.tool_prompt import DELIVERY_PROMPT
from loguru import logger

def delivery_action(number: str):
    try:
        # breakpoint()
        query = f'number={number}&mobile=mobile&type=type'

        url = user_config.TOOL_DELIVERY_BASE_URL + '?' + query
        headers = {
            'Authorization': 'APPCODE ' + user_config.TOOL_DELIVERY_API_KEY
        }

        request = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(request, context=ctx) as response:
            content = response.read().decode('utf-8')
            content = json.loads(content)

            company = content['data'].get('typename')
            result = []
            for data in content['data']['list']:
                result.append(f"时间为{data.get('time')}, 快递信息是: {data.get('status')}")
            result.reverse()
            final_result = DELIVERY_PROMPT.format(company, number, result)
            logger.info(f"------执行API------\n {final_result}")
            return final_result
    except Exception as err:
        logger.error(f"delivery action appear: {err}")
        return "查询快递信息有误，请检查您输入的快递信息是否正确"