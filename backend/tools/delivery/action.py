import urllib.request
import urllib.parse
import ssl
import json
from typing import Type
from langchain.tools import BaseTool
from pydantic import Field, BaseModel
from settings import app_settings
from prompts.tool_prompt import DELIVERY_PROMPT
from loguru import logger

class DeliveryInput(BaseModel):
    delivery_number: str = Field(description='用户输入的快递单号')

class DeliveryTool(BaseTool):
    name = 'delivery'
    description = '用来查询用户的快递物流信息'
    args_schema: Type[BaseModel] = DeliveryInput

    def _run(self, delivery_number: str):
        return get_delivery(delivery_number)


# 支持function call的模型
def get_delivery(delivery_number: str):
    """用来查询用户的快递物流信息"""
    try:
        query = f'number={delivery_number}&mobile=mobile&type=type'

        url = app_settings.tool_delivery.get('endpoint') + '?' + query
        headers = {
            'Authorization': 'APPCODE ' + app_settings.tool_delivery.get('api_key')
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
            final_result = DELIVERY_PROMPT.format(company, delivery_number, result)
            logger.info(f"------执行API------\n {final_result}")
            return final_result
    except Exception as err:
        logger.error(f"delivery action appear: {err}")
        return "查询快递信息有误，请检查您输入的快递信息是否正确"
