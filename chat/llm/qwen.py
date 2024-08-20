import random
from http import HTTPStatus
from dashscope import Generation
from langchain.schema import HumanMessage
from config.llm_config import QWEN_API_KEY, QWEN_NAME
from loguru import logger

def call_with_messages():
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': '你是谁？'}]
    response = Generation.call(model="qwen-plus",
                               messages=messages,
                               # 设置随机数种子seed，如果没有设置，则随机数种子默认为1234
                               seed=random.randint(1, 10000),
                               temperature=0.8,
                               api_key="",
                               top_p=0.8,
                               top_k=50,
                               # 将输出设置为"message"格式
                               result_format='message')
    if response.status_code == HTTPStatus.OK:
        print(response)
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))


# 直接调用模型对话
def llm_chat(prompt):
    messages = [HumanMessage(content=prompt)]
    response = Generation.call(model=QWEN_NAME,
                               messages=messages,
                               temperature=0.8,
                               api_key=QWEN_API_KEY,
                               # 将输出设置为"message"格式
                               result_format='message')
    try:
        logger.info(f"llm chat return message: {response.output.choices[0]['message']['content']} HTTPStatus: {response.status_code}")
        return response.output.choices[0]['message']['content']
    except Exception as err:
        logger.error(f"llm chat error: {err}")