from typing import List
from type.message import Message
from llm.openai import llm_function_call, llm_chat
from prompt.template import function_call_template, ask_user_template, action_template
from prompt.llm_prompt import fail_action_prompt
from langchain.prompts import PromptTemplate
from database.base import Agent
from processor.impl import BotCheck
from action import action_class
from loguru import  logger

class ChatbotModel:
    def __init__(self):
        self.historyMessage: List[Message] = []

    def include_history_message(self, message: Message):
        """try history message include this ChatbotModel class"""
        self.historyMessage.append(message)

    def get_history_message(self):
        return self.historyMessage

    def run(self, user_input: str, historyMessage: List[Message], agent: str):

        breakpoint()
        function = Agent.get_parameter_by_name(agent)

        prompt_template = PromptTemplate.from_template(function_call_template)
        prompt_history = ""
        
        for msg in historyMessage:
            prompt_history = prompt_history + msg.to_str()

        final_prompt = prompt_template.format(user_input=user_input, history=prompt_history)
        function_name, function_args = llm_function_call(final_prompt, function)

        # 直接与模型对话，不调用function
        if function_name is None or function_name not in action_class:
            return llm_chat(final_prompt)

        if BotCheck.slot_is_full(function_args, function_name):
            logger.info("parameters is full !")
            # 判断是否是自定义Agent
            if Agent.check_name_iscustom(function_name):
                action_result = self.custom_action(function_name, function_args)
            else:
                action_result = self.action(function_name, function_args)

            action_prompt_template = PromptTemplate.from_template(action_template)
            action_prompt = action_prompt_template.format(user_input=user_input, scene=function_name, action_result=action_result)
            
            return llm_chat(action_prompt)
        else:
            lack_parameter = BotCheck.lack_parameters(function_args, function_name)
            have_parameter = BotCheck.have_parameters(function_args)

            ask_user_prompt_template = PromptTemplate.from_template(ask_user_template)
            ask_user_prompt = ask_user_prompt_template.format(user_input=user_input, scene=function_name, have_parameters=have_parameter, parameters=lack_parameter)

            return llm_chat(ask_user_prompt)
    
    def action(self, function_name, function_args):
        try:
            action = action_class[function_name]
            result = action(**function_args)
            return result
        except Exception as err:
            logger.error(f"action appear error: {err}")
            return fail_action_prompt

    def custom_action(self, function_name, function_args):
        try:
            function_code = Agent.get_code_by_name(name=function_name)

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