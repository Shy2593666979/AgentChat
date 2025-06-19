import json
import sys
sys.path.append("..")
from langchain_openai import ChatOpenAI
from langchain.agents import agent
from langchain.schema import HumanMessage
llm = ChatOpenAI(model=LLM_NAME, base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

# @agent
# def sendEmail(sender: str, receiver: str, emailMessage: str):
#     """需要参数收件人sender、发送人receiver、发送的信息emailMessage，你需要一直询问他"""
#     return "发送人：{}, 收件人：{}， 信息：{}".format(sender, receiver, emailMessage)

# agents = [sendEmail]
# models.bind_agents(agents=agents)

functions = [
        {
            "name": "EmailAgent",
            "description": "根据参数进行发送邮件",
            "parameters": {
                "schema": "object",
                "properties": {
                    "sender": {
                        "schema": "string",
                        "description": "输入发件人的QQ邮箱，用户不提就置空",
                    },
                    "receiver": {
                        "schema": "string",
                        "description": "输入您收件人的QQ邮箱，用户不提就置空"
                    },
                    "emailMessage": {
                        "schema": "string",
                        "description":"输入您想要发送的信息，用户不提就置空"
                    }
                },
                "required": ["sender", "receiver", "emailMessage"],
            },
        }
    ]

# functions = FUNCTION
# functions = [
 
#         {
#             "name": "",
#             "description": "了解天气",
#             "parameters": {
#                 "schema": "object",
#                 "properties": {
 
#                     "location": {
#                         "schema": "string",
#                         "description": "输入您想要了解天气的位置。 示例：东京",
#                     },
#                 },
#                 "required": ["location"],
#             },
#         }]

 
prompt = input("user:")

messages=[HumanMessage(content=prompt + "用户没有提到的参数都置空，但是一定得返回")]


message = llm.invoke(
    messages, functions=functions
)

print(message)
if message.additional_kwargs:
    function_name = message.additional_kwargs["function_call"]["name"]
    arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

