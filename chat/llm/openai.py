import json
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from config.llm_config import LLM_API_KEY, LLM_BASE_URL, LLM_NAME
from prompt.llm_prompt import function_call_prompt
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from langchain.prompts import PromptTemplate
from config.langfuse_config import LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
from config.langfuse_config import FUNCTION_TRACE_NAME, CHAT_TRACE_NAME, USER_ID
from config import user_config

INCLUDE_MSG = {"content", "id"}



class LLMChat:

    # 目前只支持function的LLM调用，后续可能会加上React框架，支持全模型调用
    @classmethod
    async def llm_function_call(cls, prompt, function: str):
        llm = ChatOpenAI(model=user_config.LLM_OPENAI_MODEL,
                         base_url=user_config.LLM_OPENAI_BASE_URL,
                         api_key=user_config.LLM_OPENAI_API_KEY)

        # 使用langfuse进行监控对话的流程
        function_call_handler = CallbackHandler(
            trace_name=user_config.LANGFUSE_FUNCTION_TRACE_NAME,
            user_id=user_config.LANGFUSE_USER_ID,
            host=user_config.LANGFUSE_HOST,
            secret_key=user_config.LANGFUSE_SECRET_KEY,
            public_key=user_config.LANGFUSE_PUBLIC_KEY
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
        llm = ChatOpenAI(model=user_config.LLM_OPENAI_MODEL,
                         base_url=user_config.LLM_OPENAI_BASE_URL,
                         api_key=user_config.LLM_OPENAI_API_KEY)

        # 使用langfuse 监控对话的流程
        llm_chat_handler = CallbackHandler(
            trace_name=CHAT_TRACE_NAME,
            user_id=USER_ID,
            host=LANGFUSE_HOST,
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY
        )

        chain = prompt | llm
        async for chunk in chain.astream({**kwargs}, config={"callbacks": [llm_chat_handler]}):
            # 数据按照json的格式转发，只包括content、id参数
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)
