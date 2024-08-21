import json
import os
from database.base import Agent
from loguru import  logger

# 打印当前工作目录
# print("Current working directory:", os.getcwd())

def get_function(type: str="openai"):
    if type == "openai":
        return get_function_openai()
    else:
        return get_function_qwen()

def get_function_openai():
    parameter = Agent.select_agent_by_type(type="openai")
    result = []
    for data in parameter:

        para = json.loads(data.parameter)
        result.append(para)
    return result

def get_function_qwen():
    parameter = Agent.select_agent_by_type(type="qwen")
    result = []
    for data in parameter:
        para = json.loads(data.parameter)
        result.append(para)
    return result

def get_function_by_name_type(function_name: str, type: str="openai"):
    parameter = Agent.get_agent_by_name_type(name=function_name, type=type)

    for data in parameter:
        para = json.loads(data.parameter)
        return para
    logger.info(f"get function by name type appear no data")