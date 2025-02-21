# -------------------------------
# 该文件目前版本已弃用
# -------------------------------
import json
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from prompts.llm_prompt import function_call_prompt
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from langchain.prompts import PromptTemplate
from settings import app_settings

INCLUDE_MSG = {"content", "id"}



class LLMChat:

    # 目前只支持function的LLM调用，后续可能会加上React框架，支持全模型调用
    @classmethod
    async def llm_function_call(cls, prompt, function: str):
        llm = ChatOpenAI(model=app_settings.llm.get('model_name'),
                         base_url=app_settings.llm.get('base_url'),
                         api_key=app_settings.llm.get('api_key'))

        # 使用langfuse进行监控对话的流程
        function_call_handler = CallbackHandler(
            trace_name=app_settings.langfuse.get('trace_name'),
            user_id=app_settings.langfuse.get('user_id'),
            host=app_settings.langfuse.get('host'),
            secret_key=app_settings.langfuse.get('secret_key'),
            public_key=app_settings.langfuse.get('public_key')
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

    # 调用模型对话
    @classmethod
    async def llm_chat(cls, template: str, **kwargs):

        prompt_template = PromptTemplate.from_template(template)

        # final_result = ''
        # message = llm.invoke(messages, config={"callbacks": [llm_chat_handler]})
        async for one_result in cls.astream_chat(prompt_template, **kwargs):
            # final_result += one_result.content
            yield one_result

    # 流式输出
    @classmethod
    async def astream_chat(cls, prompt, **kwargs):
        llm = ChatOpenAI(model=app_settings.llm.get('model_name'),
                         base_url=app_settings.llm.get('base_url'),
                         api_key=app_settings.llm.get('api_key'))

        # 使用langfuse 监控对话的流程
        llm_chat_handler = CallbackHandler(
            trace_name=app_settings.langfuse.get('trace_name'),
            user_id=app_settings.langfuse.get('user_id'),
            host=app_settings.langfuse.get('host'),
            secret_key=app_settings.langfuse.get('secret_key'),
            public_key=app_settings.langfuse.get('public_key')
        )

        chain = prompt | llm
        async for chunk in chain.astream({**kwargs}, config={"callbacks": [llm_chat_handler]}):
            # 数据按照json的格式转发，只包括content、id参数
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
