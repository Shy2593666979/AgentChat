import asyncio
import json

from fastapi import WebSocket, status, Request
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from loguru import logger

from prompt.llm_prompt import agent_guide_word
from service.agent import AgentService
from service.user import UserPayload
from service.llm import LLMService

class State(TypedDict):
    name: str
    description: str
    user_input: str


def resp_state(name: str = '', description: str = '', user_input: str = ''):
    return {"name": name, "description": description, "user_input": user_input}


class AutoBuildClient:
    def __init__(self, chat_id: str, user_id: str, client_key: str,
                 login_user: UserPayload, websocket: WebSocket, **kwargs):
        self.client_key = client_key
        self.chat_id = chat_id
        self.user_id = user_id
        self.login_user = login_user
        self.websocket = websocket
        self.builder = StateGraph(State)


    async def send_message(self, message: str):
        return self.websocket.send_text(message)

    async def send_json(self, message: dict):
        return self.websocket.send_json(message)

    async def auto_chat(self):
        pass

    async def send_guide_word(self):
        return await self.send_message(agent_guide_word)

    async def init_graph(self):
        async def check_model_exist():
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
            resp = await self.abstract_name(user_input=state['user_input'])
            try:
                data = json.loads(resp)
                name = data.get('name')
                return resp_state(name=name, description=state['description'], user_input=state['user_input'])
            except Exception as err:
                logger.error(f'abstract llm response name: {err}')
                return resp_state(name=state['user_input'], description=state['description'],
                                  user_input=state['user_input'])

        async def abstract_description(state):
            resp = await self.abstract_description(user_input=state['user_input'])
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

        async def auto_create_assistant(state):
            name = state['name']
            description = state['description']

            # 这里是通过Function Call的方式给Agent绑定LLM、Tool
            await self.send_message('正在为您创建Agent中...............')

        # 首先判断是否有可使用的大模型
        await check_model_exist()

        # 添加LangGraph的节点
        self.builder.add_node('send_guide_word', send_guide_word)
        self.builder.add_node('receive_input_name', receive_input_name)
        self.builder.add_node('receive_input_description', receive_input_description)
        # self.builder.add_node('ask_user_name', ask_user_name)
        self.builder.add_node('ask_user_description', ask_user_description)
        self.builder.add_node('abstract_name', abstract_name)
        self.builder.add_node('abstract_description', abstract_description)
        # self.builder.add_node('check_repeat_name', check_repeat_name)
        self.builder.add_node('auto_create_assistant', auto_create_assistant)

        # 增加LangGraph的边
        self.builder.add_edge(START, 'send_guide_word')
        self.builder.add_edge('send_guide_word', 'receive_input_name')
        self.builder.add_edge('receive_input_name', 'abstract_name')
        self.builder.add_conditional_edges('abstract_name', check_repeat_name)
        self.builder.add_edge('ask_user_description', 'receive_input_description')
        self.builder.add_edge('receive_input_description', 'abstract_description')
        self.builder.add_edge('abstract_description', 'auto_create_assistant')
        self.builder.add_edge('auto_create_assistant', END)

        auto_workflow = self.builder.compile()
        await auto_workflow.ainvoke(input=resp_state())


