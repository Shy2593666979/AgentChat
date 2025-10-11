import asyncio
import json

from fastapi import WebSocket
from typing import TypedDict, List, Dict

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from loguru import logger
from pydantic import BaseModel, Field

from agentchat.prompts.llm import agent_guide_word, auto_build_ask_prompt, auto_build_abstract_prompt, create_agent_prompt, \
    PROMPT_REACT_BASE
from agentchat.api.services.agent import AgentService
from agentchat.api.services.chat import ChatService
from agentchat.api.services.tool import ToolService
from agentchat.api.services.user import UserPayload
from agentchat.api.services.llm import LLMService, React_provider
from agentchat.tools import action_Function_call


class State(TypedDict):
    name: str
    description: str
    user_input: str

class AgentBaseModel(BaseModel):
    name: str = Field(description='想要创建Agent的名称')
    description: str = Field(description='想要创建Agent的描述信息')

def resp_state(name: str = '', description: str = '', user_input: str = ''):
    return {"name": name, "description": description, "user_input": user_input}


class AutoBuildClient:
    def __init__(self, chat_id: str, client_key: str,
                 login_user: UserPayload, websocket: WebSocket, **kwargs):
        self.client_key = client_key
        self.chat_id = chat_id
        self.login_user = login_user
        self.websocket = websocket
        self.builder_graph = StateGraph(State)
        self.base_agent = None
        self.parser = None
        self.abstract_prompt = None
        self.abstract_agent = None

        asyncio.run(self._run_start())

    async def _run_start(self):
        # 检查是否有可用模型
        await self.check_model_exist()

        # 初始化提取参数Agent
        await self.init_abstract_agent()

        # 初始化Multi-Agents流程图
        await self.init_graph()

    async def init_abstract_agent(self):
        self.parser = JsonOutputParser(pydantic_object=AgentBaseModel)
        self.abstract_prompt = PromptTemplate(
            template=auto_build_abstract_prompt,
            input_variables=["input", "history"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.abstract_agent = self.abstract_prompt | self.base_agent | self.parser

    async def send_message(self, message: str):
        return self.websocket.send_text(message)

    async def send_json(self, message: dict):
        return self.websocket.send_json(message)

    async def run_chat(self):
        auto_workflow = self.builder_graph.compile()
        await auto_workflow.ainvoke(input=resp_state())

    async def send_guide_word(self):
        return await self.send_message(agent_guide_word)

    async def check_model_exist(self):
        # 获得可用的模型
        llm = LLMService.get_one_llm()
        if llm is None:
            await self.send_message(message='没找到可用的大模型')
            raise ValueError(f'No large models available')
        else:
            model = llm.model
            base_url = llm.base_url
            api_key = llm.api_key
            # 创建Agent的构建方式
            await self.create_build_agent(model=model, api_key=api_key, base_url=base_url)

    async def ask_user_message(self, user_input, para_type):
        prompt = auto_build_ask_prompt.format(user_input=user_input, para_type=para_type)

        resp = self.base_agent.ainvoke(input=prompt).content
        return resp

    async def create_build_agent(self, **kwargs):
        self.base_agent = ChatOpenAI(**kwargs)

    async def abstract_parameter(self, user_input):
        resp = await self.abstract_agent.ainvoke({"input": user_input, "history": ""})

        return resp.content

    async def create_agent(self, name: str, description: str):
        llm = LLMService.get_one_llm()

        tools = []
        tools_name = []
        for key, func in action_Function_call:
            tools_name.append(key)
            tools.append(ChatService.function_to_json(func))

        # 检查是否走React 还是 Fun call
        if llm.model in React_provider:
            funcs = await self._func_react(user_input=description, tools=tools, tools_name=tools_name)
        else:
            # 这里可以优化的是将Tools Parameter中的required 字段给去掉
            prompt = create_agent_prompt.format(description=description)
            funcs, _ = await self._function_call(user_input=prompt, tools=tools)
            funcs = json.loads(funcs)

        tools_id = []
        for func in funcs:
            # 根据工具名称去查ID
            tool_id = ToolService.get_id_by_tool_name(func, self.login_user.user_id)
            tools_id.append(tool_id)
            
        
        AgentService.create_agent(
            name=name,
            logo='img/agent/assistant.png',
            description=description,
            llm_id=llm.llm_id,
            tool_id=tools_id,
            user_id=self.login_user.user_id,
        )
    
    async def _function_call(self, user_input: str, tools: List[Dict]):
        messages = [HumanMessage(content=user_input)]
        message = self.base_agent.ainvoke(
            messages,
            functions=tools,
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

    async def _func_react(self, user_input: str, tools: List[Dict], tools_name: List[str]):
        def parse_tools_call(text):
            tool_name, tool_args = '', ''
            i = text.rfind('\nAction:')
            j = text.rfind('\nAction Input:')
            k = text.rfind('\nObservation:')
            if 0 <= i < j:  # If the text has `Action` and `Action input`,
                if k < j:  # but does not contain `Observation`,
                    # then it is likely that `Observation` is ommited by the LLM,
                    # because the output text may have discarded the stop word.
                    text = text.rstrip() + '\nObservation:'  # Add it back.
                k = text.rfind('\nObservation:')
                tool_name = text[i + len('\nAction:'): j].strip()
                tool_args = text[j + len('\nAction Input:'): k].strip()
                text = text[:k]
            return tool_name, tool_args, text

        prompt = PROMPT_REACT_BASE.format(tools_text=tools, tools_name_text=tools_name, query=user_input)
        resp = self.base_agent.invoke(input=prompt).content

        tools_name, _, _ = parse_tools_call(resp)

        return tools_name



    async def init_graph(self):

        async def send_guide_word(state):
            """自动发送开场白"""
            await self.send_guide_word()
            return resp_state(name=state['name'], description=state['description'], user_input=state['user_input'])

        async def receive_input_name(state):
            while True:
                try:
                    json_payload_receive = await asyncio.wait_for(self.websocket.receive_json(),
                                                                  timeout=2.0)
                except asyncio.TimeoutError:
                    continue
                try:
                    payload = json.loads(json_payload_receive) if json_payload_receive else {}
                    payload = payload.get('user_input', '')
                except TypeError:
                    payload = json_payload_receive['user_input']

                return resp_state(name=state['name'], description=state['description'], user_input=payload)

        async def receive_input_description(state):
            while True:
                try:
                    json_payload_receive = await asyncio.wait_for(self.websocket.receive_json(),
                                                                  timeout=2.0)
                except asyncio.TimeoutError:
                    continue
                try:
                    payload = json.loads(json_payload_receive) if json_payload_receive else {}
                    payload = payload.get('user_input', '')
                except TypeError:
                    payload = json_payload_receive['user_input']
                return resp_state(name=state['name'], description=state['description'], user_input=payload)

        async def ask_user_name(state):
            """询问应用的名称"""
            response = await self.ask_user_message(user_input=state['user_input'], para_type='name')
            await self.send_message(message=response)

        async def ask_user_description(state):
            """询问应用的具体描述"""
            response = await self.ask_user_message(user_input=state['user_input'], para_type='description')
            await self.send_message(message=response)

        async def abstract_name(state):
            resp = await self.abstract_parameter(user_input=state['user_input'])
            try:
                data = json.loads(resp)
                name = data.get('name')
                return resp_state(name=name, description=state['description'], user_input=state['user_input'])
            except Exception as err:
                logger.error(f'abstract llm response name: {err}')
                return resp_state(name=state['user_input'], description=state['description'],
                                  user_input=state['user_input'])

        async def abstract_description(state):
            resp = await self.abstract_parameter(user_input=state['user_input'])
            try:
                data = json.loads(resp)
                description = data.get('description')
                return resp_state(name=state['name'], description=description, user_input=state['user_input'])
            except Exception as err:
                logger.error(f'abstract llm response description: {err}')
                return resp_state(name=state['name'], description=state['user_input'], user_input=state['user_input'])

        # LangGraph循环图中的判断条件
        async def check_repeat_name(state):
            """pass"""
            if AgentService.check_repeat_name(name=state['user_input'], user_id=self.login_user.user_id):
                await self.send_message(message='应用名称已经存在，请更换一个应用名称')
                return 'receive_input_name'
            else:
                return 'ask_user_description'

        async def auto_create_agent(state):
            name = state['name']
            description = state['description']

            # 这里是通过Function Call的方式给Agent绑定LLM、Tool
            await self.send_message('正在为您创建Agent中...............')

            await self.create_agent(name, description)
            await self.send_message('Agent创建成功！！！')

        # 添加LangGraph的节点
        self.builder_graph.add_node('send_guide_word', send_guide_word)
        self.builder_graph.add_node('receive_input_name', receive_input_name)
        self.builder_graph.add_node('receive_input_description', receive_input_description)
        # self.builder_graph.add_node('ask_user_name', ask_user_name)
        self.builder_graph.add_node('ask_user_description', ask_user_description)
        self.builder_graph.add_node('abstract_name', abstract_name)
        self.builder_graph.add_node('abstract_description', abstract_description)
        # self.builder_graph.add_node('check_repeat_name', check_repeat_name)
        self.builder_graph.add_node('auto_create_agent', auto_create_agent)

        # 增加LangGraph的边
        self.builder_graph.add_edge(START, 'send_guide_word')
        self.builder_graph.add_edge('send_guide_word', 'receive_input_name')
        self.builder_graph.add_edge('receive_input_name', 'abstract_name')
        self.builder_graph.add_conditional_edges('abstract_name', check_repeat_name)
        self.builder_graph.add_edge('ask_user_description', 'receive_input_description')
        self.builder_graph.add_edge('receive_input_description', 'abstract_description')
        self.builder_graph.add_edge('abstract_description', 'auto_create_agent')
        self.builder_graph.add_edge('auto_create_assistant', END)







