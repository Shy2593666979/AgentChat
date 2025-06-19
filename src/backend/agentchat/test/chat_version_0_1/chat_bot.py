# -------------------------------
# 该文件目前版本已弃用
# -------------------------------
import json
from typing import List
from schema.message import Message
from test.version_0_1.openai import LLMChat
from prompts.template import function_call_template, ask_user_template, action_template, llm_chat_template
from prompts.llm_prompt import fail_action_prompt
from langchain.prompts import PromptTemplate
from api.services.agent import AgentService
from test.version_0_1.impl import BotCheck
from tools import action_Function_call
from loguru import logger

class ChatbotModel:
    def __init__(self):
        self.historyMessage: List[Message] = []
        self.final_result: str = ''
    
    def include_history_message(self, message: Message):
        """try history message include this ChatbotModel class"""
        self.historyMessage.append(message)

    def get_history_message(self):
        return self.historyMessage

    async def run(self, user_input: str, historyMessage: List[Message], agent: str):
        
        # 获取当前对话窗口的历史记录
        # breakpoint()
        prompt_history = ""
        for msg in historyMessage:
            prompt_history = prompt_history + msg.to_str()

        # 不调用任何Function直接进行大模型对话
        if agent not in action_Function_call and not AgentService.check_name_iscustom(agent):
            async for one_result in LLMChat.llm_chat(llm_chat_template, user_input=user_input, history=prompt_history):
                self.final_result += json.loads(one_result)['content']
                yield one_result
            # 执行这个if 就结束
            return 
        
        # 调用Function
        function = AgentService.get_parameter_by_name(agent)

        prompt_template = PromptTemplate.from_template(function_call_template)

        final_prompt = prompt_template.format(user_input=user_input, history=prompt_history)
        function_name, function_args = await LLMChat.llm_function_call(final_prompt, function)

        # 直接与模型对话，不调用function
        if function_name is None:
            async for one_result in LLMChat.llm_chat(llm_chat_template, user_input=user_input, history=prompt_history):
                self.final_result += json.loads(one_result)['content']
                yield one_result
        else:

            if BotCheck.slot_is_full(function_args, function_name):
                logger.info("parameters is full !")
                # 判断是否是自定义Agent
                if AgentService.check_name_iscustom(function_name):
                    action_result = self.custom_action(function_name, function_args)
                else:
                    action_result = self.action(function_name, function_args)

                # action_prompt_template = PromptTemplate.from_template(action_template)
                # action_prompt = action_prompt_template.format(user_input=user_input, function_name=function_name, action_result=action_result)
                
                async for one_result in LLMChat.llm_chat(action_template, user_input=user_input, function_name=function_name, action_result=action_result):
                    self.final_result += json.loads(one_result)['content']
                    yield one_result
            else:
                logger.info("parameters is lack !")
                lack_parameters = BotCheck.lack_parameters(function_args, function_name)
                have_parameters = BotCheck.have_parameters(function_args)

                # ask_user_prompt_template = PromptTemplate.from_template(ask_user_template)
                # ask_user_prompt = ask_user_prompt_template.format(user_input=user_input, function_name=function_name, have_parameters=have_parameters, parameters=lack_parameters)
                
                async for one_result in LLMChat.llm_chat(ask_user_template, user_input=user_input, function_name=function_name, have_parameters=have_parameters, lack_parameters=lack_parameters):
                    self.final_result += json.loads(one_result)['content']
                    yield one_result
    
    def action(self, function_name, function_args):
        try:
            action = action_Function_call[function_name]
            result = action(**function_args)
            return result
        except Exception as err:
            logger.error(f"action appear error: {err}")
            return fail_action_prompt

    def custom_action(self, function_name, function_args):
        try:
            function_code = AgentService.get_code_by_name(name=function_name)

            # 编译字符串为代码对象
            compiled_code = compile(function_code, '<string>', 'exec')
            # 执行代码对象
            exec(compiled_code)
            # 调用函数
            result = custom_function(**function_args)
            return result
        except Exception as err:
            logger.error(f"custom action appear error: {err}")
            return fail_action_prompt
