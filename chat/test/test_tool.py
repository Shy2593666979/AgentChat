import json
import sys
sys.path.append("..")
from langchain_openai import ChatOpenAI
from langchain.agents import agent
from config.llm_config import LLM_NAME, LLM_BASE_URL, LLM_API_KEY
from langchain.schema import HumanMessage
from agents import FUNCTION
llm = ChatOpenAI(model=LLM_NAME, base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

# @agent
# def sendEmail(sender: str, receiver: str, emailMessage: str):
#     """需要参数收件人sender、发送人receiver、发送的信息emailMessage，你需要一直询问他"""
#     return "发送人：{}, 收件人：{}， 信息：{}".format(sender, receiver, emailMessage)

# agents = [sendEmail]
# model.bind_agents(agents=agents)

# functions = [
 
#         {
#             "name": "send_email",
#             "description": "发送邮箱",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "sender": {
#                         "type": "string",
#                         "description": "输入发件人的QQ邮箱，用户不提就置空",
#                     },
#                     "receiver": {
#                         "type": "string",
#                         "description": "输入您收件人的QQ邮箱，用户不提就置空"
#                     },
#                     "emailMessage": {
#                         "type": "string",
#                         "description":"输入您想要发送的信息，用户不提就置空"
#                     }
#                 },
#                 "required": ["sender", "receiver", "emailMessage"],
#             },
#         }
#     ]
functions = FUNCTION
# functions = [
 
#         {
#             "name": "weather",
#             "description": "了解天气",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
 
#                     "location": {
#                         "type": "string",
#                         "description": "输入您想要了解天气的位置。 示例：东京",
#                     },
#                 },
#                 "required": ["location"],
#             },
#         }]

 
prompt = input("user:")

messages=[HumanMessage(content=prompt + "用户没有提到的参数都置空，但是一定得返回")]


message = llm.invoke(
    messages
)

print(message.content)
if message.additional_kwargs:
    function_name = message.additional_kwargs["function_call"]["name"]
    arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

