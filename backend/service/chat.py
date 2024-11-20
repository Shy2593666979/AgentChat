from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from data.llm import Function_Call_provider, React_provider
from prompt.llm_prompt import react_prompt_en, fail_action_prompt
from prompt.template import function_call_template
from service.tool import ToolService
from tools import action_Function_call, action_React
from service.llm import LLMService
from loguru import logger
import inspect
import json


class ChatClient:
    def __init__(self, **kwargs):
        self.llm_id = kwargs.get('llm_id')
        self.tools_id = kwargs.get('tool_id')
        self.llm_call = None
        self.llm = None
        self.tools = []
        self.init_llm()
        self.init_tools()

    def init_llm(self):
        llm_config = LLMService.get_llm_by_id(llm_id=self.llm_id)

        self.llm = ChatOpenAI(model=llm_config.model,
                              base_url=llm_config.base_url, api_key=llm_config.api_key)

        self.llm_call = 'Function Call' if llm_config.model in Function_Call_provider else 'React'

    def init_tools(self):
        tools_name = ToolService.get_tool_name_by_id(self.tools_id)
        if self.llm_call == 'React':
            for name in tools_name:
                func = action_React[name]
                self.tools.append(function_to_json(func))
        else:
             for name in tools_name:
                self.tools.append(action_Function_call[name])

    def run(self, user_input):
        if self.llm_call == 'React':
            return self._run_react(user_input)
        else:
            return self._run_function_call(user_input)

    def _run_react(self, user_input):
        agent = create_structured_chat_agent(llm=self.llm, tools=self.tools, prompt=react_prompt_en)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

        async for chunk in agent_executor.astream({'input': {}}):
            yield chunk.json()

    def _run_function_call(self, user_input: str):

        fun_name, args = self._function_call(user_input=user_input)

        tools_result = self._exec_tools(fun_name, args)
        prompt_template = PromptTemplate.from_template(function_call_template)

        chain = prompt_template | self.llm
        async for chunk in chain.astream({'input': {}, 'history': {}, 'tools': tools_result}):
            yield chunk.json()

    def _function_call(self, user_input: str):
        messages = [HumanMessage(content=user_input)]
        message = self.llm.invoke(
            messages,
            functions=self.tools,
        )
        try:
            if message.additional_kwargs:
                function_name = message.additional_kwargs["function_call"]["name"]
                arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

                logger.info(f"function call result: \n function_name: {function_name} \n arguments: {arguments}")

                return function_name, arguments
        except Exception as err:
            logger.info(f"function call is not appear: {err}")
            return None, None

    def _exec_tools(self, func_name, args):
        try:
            action = action_Function_call[func_name]
            result = action(**args)
            return result
        except Exception as err:
            logger.error(f"action appear error: {err}")
            return fail_action_prompt

def function_to_json(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
