import asyncio
import json
import sys

from langchain_core.prompts import PromptTemplate

sys.path.append("..")
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from config.llm_config import LLM_API_KEY, LLM_BASE_URL, LLM_NAME
from orjson import orjson
from prompts.llm_prompt import function_call_prompt
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from config.langfuse_config import LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
from config.langfuse_config import FUNCTION_TRACE_NAME, CHAT_TRACE_NAME, USER_ID
from pydantic import BaseModel

llm = ChatOpenAI(model=LLM_NAME, base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

class StreamData(BaseModel):
    data: dict | str

    def __str__(self) -> str:
        if isinstance(self.data, dict):
            return f'data: {orjson.dumps(self.data).decode()}\n\n'
        return f'data: {self.data}\n\n'


# 目前只支持function的LLM调用，后续可能会加上React框架，支持全模型调用
def llm_function_call(prompt, function: str):
    # 使用langfuse进行监控对话的流程
    function_call_handler = CallbackHandler(
        trace_name=FUNCTION_TRACE_NAME,
        user_id=USER_ID,
        host=LANGFUSE_HOST,
        secret_key=LANGFUSE_SECRET_KEY,
        public_key=LANGFUSE_PUBLIC_KEY
    )
    prompt = prompt + function_call_prompt

    messages = [HumanMessage(content=prompt)]
    message = llm.invoke(
        messages,
        functions=[json.loads(function)],
        config={"callbacks": [function_call_handler]}
    )

    logger.info(f"function call all message: {message}")
    try:
        if message.additional_kwargs:
            function_name = message.additional_kwargs["function_call"]["name"]
            arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

            logger.info(f"function call result: \n function_name: {function_name} \n arguments: {arguments}")

            return function_name, arguments
    except Exception as err:
        logger.info(f"function call is not appear: {err}")
        return None, None

# # 直接调用模型对话
# async def llm_chat(prompts):
#     # # 使用langfuse 监控对话的流程
#     # llm_chat_handler = CallbackHandler(
#     #     trace_name=CHAT_TRACE_NAME,
#     #     user_id=USER_ID,
#     #     host=LANGFUSE_HOST,
#     #     secret_key=LANGFUSE_SECRET_KEY,
#     #     public_key=LANGFUSE_PUBLIC_KEY
#     # )
#
#     # messages = [HumanMessage(content=prompts)]
#     # message = llm.invoke(messages, config={"callbacks": [llm_chat_handler]})
#
#     # 流式生成提示词
#     print("qqqq")
#     final_prompt = ''
#     async for one_prompt in chat_llm(prompts):
#         print(final_prompt)
#         yield str(StreamData(event='message', data={'schema': 'prompts', 'message': one_prompt.content}))
#         final_prompt += one_prompt.content
#
#     yield str(StreamData(event='message', data={'schema': 'end', 'message': ""}))
#
#
#
# async def chat_llm(prompts):
#     chain = llm
#     async for one in chain.astream(prompts):
#         yield one
#
# print("121")
# asyncio.run(llm_chat(prompts="你好啊"))



async def llm_chat(prompt):
    # 使用langfuse 监控对话的流程
    llm_chat_handler = CallbackHandler(
        trace_name=CHAT_TRACE_NAME,
        user_id=USER_ID,
        host=LANGFUSE_HOST,
        secret_key=LANGFUSE_SECRET_KEY,
        public_key=LANGFUSE_PUBLIC_KEY
    )

    # 流式生成提示词
    final_prompt = ''
    async for one_prompt in chat_llm(prompt, user="你好啊"):
        yield str({'schema': 'prompts', 'message': one_prompt.content})
        final_prompt += one_prompt.content
    yield str({'schema': 'end', 'message': ""})
    yield str(final_prompt)

async def chat_llm(prompt, **kwargs):
    prompt = PromptTemplate.from_template(prompt)

    llm_chat_handler = CallbackHandler(
        trace_name=CHAT_TRACE_NAME,
        user_id=USER_ID,
        host=LANGFUSE_HOST,
        secret_key=LANGFUSE_SECRET_KEY,
        public_key=LANGFUSE_PUBLIC_KEY
    )

    chain = prompt | llm
    async for one in chain.astream({**kwargs}, config={"callbacks": [llm_chat_handler]}):
        yield one

async def print_stream(prompt):

    async for message in llm_chat(prompt):
        print(message)

# 运行异步函数
asyncio.run(print_stream(prompt="这是用户说的话: {user}"))

