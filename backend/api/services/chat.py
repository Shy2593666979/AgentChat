from uuid import uuid4

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from api.services.llm import Function_Call_provider
from prompts.llm_prompt import react_prompt_en, fail_action_prompt, function_call_prompt
from prompts.template import function_call_template
from api.services.history import HistoryService
from api.services.tool import ToolService
from tools import action_Function_call, action_React
from api.services.llm import LLMService
from loguru import logger
import chromadb
import inspect
import json

INCLUDE_MSG = {"content", "id"}

class ChatService:
    def __init__(self, **kwargs):
        self.llm_id = kwargs.get('llm_id')
        self.tools_id = kwargs.get('tool_id')
        self.dialog_id = kwargs.get('dialog_id')
        self.embedding_id = kwargs.get('embedding_id')
        self.llm_call = None
        self.llm = None
        self.embedding = None
        self.tools = []
        self.init_llm()
        self.init_tools()
        self.collection = chromadb.Client().get_or_create_collection(name=self.dialog_id,
                                                                     embedding_function=self.embedding)

    def init_llm(self):
        llm_config = LLMService.get_llm_by_id(llm_id=self.llm_id)
        self.llm = ChatOpenAI(model=llm_config.model,
                              base_url=llm_config.base_url, api_key=llm_config.api_key)

        self.llm_call = 'Function Call' if llm_config.model in Function_Call_provider else 'React'
        # Agent支持Embedding后初始化
        if self.embedding_id:
            self.init_embedding()

    def init_embedding(self):

        embedding_config = LLMService.get_llm_by_id(llm_id=self.embedding_id)
        self.embedding = OpenAIEmbeddings(model=embedding_config.model,
                                          base_url=embedding_config.base_url, api_key=embedding_config.api_key)

    def init_tools(self):
        tools_name = ToolService.get_tool_name_by_id(self.tools_id)
        if self.llm_call == 'React':
            for name in tools_name:
                func = action_React[name]
                self.tools.append(ChatService.function_to_json(func))
        else:
             for name in tools_name:
                self.tools.append(action_Function_call[name])

    async def run(self, user_input: str):
        history_message = self.get_history_message(user_input=user_input, dialog_id=self.dialog_id)

        if self.llm_call == 'React':
            return self._run_react(user_input, history_message)
        else:
            return self._run_function_call(user_input, history_message)

    async def _run_react(self, user_input: str, history_message: str):
        agent = create_structured_chat_agent(llm=self.llm, tools=self.tools, prompt=react_prompt_en)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

        async for chunk in agent_executor.astream({'input': user_input, 'history': history_message}):
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)

    async def _run_function_call(self, user_input: str, history_message: str):

        func_prompt = function_call_template.format(input=user_input, history=history_message)
        fun_name, args = self._function_call(user_input=func_prompt)

        tools_result = ChatService._exec_tools(fun_name, args)
        prompt_template = PromptTemplate.from_template(function_call_prompt)

        chain = prompt_template | self.llm
        async for chunk in chain.astream({'input': user_input, 'history': history_message, 'tools_result': tools_result}):
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)

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

    @staticmethod
    def _exec_tools(func_name, args):
        try:
            action = action_Function_call[func_name]
            result = action(**args)
            return result
        except Exception as err:
            logger.error(f"action appear error: {err}")
            return fail_action_prompt


    def get_history_message(self, user_input: str, dialog_id: str, top_k: int = 5) -> str:
        # 如果绑定了Embedding模型，默认走RAG检索聊天记录
        if self.embedding:
            messages = self._retrieval_history(user_input, dialog_id, top_k)
            return messages
        else:
            messages = self._direct_history(dialog_id, top_k)

            result = ''
            for message in messages:
                result += message.to_str()
            return result

    @staticmethod
    def _direct_history(dialog_id: str, top_k: int):
        messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k)
        result = []
        for message in messages:
            result.append(message)
        return result

    # 使用RAG检索的方式将最近2 * top_k条数据按照相关性排序，取其中top_k个
    def _retrieval_history(self, user_input: str, dialog_id: str, top_k: int):

        messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k * 2)

        for msg in messages:
            self.collection.add(documents=[msg.to_str()], ids=[uuid4().hex])

        results = self.collection.query(query_texts=[user_input], n_results=top_k)
        history = ''.join(results['documents'][0])
        return history

    @staticmethod
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
                    f"Unknown schema annotation {param.annotation} for parameter {param.name}: {str(e)}"
                )
            parameters[param.name] = {"schema": param_type}

        required = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect._empty
        ]

        return {
            "schema": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": {
                    "schema": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }
