import uuid

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

from loguru import logger

from agentchat.services.autobuild.client import AutoBuildClient
from agentchat.api.services.user import UserPayload
from agentchat.utils.helpers import get_cache_key


class AutoBuildManager:

    def __init__(self):
        self.active_connections = Dict[str, WebSocket] = {}

        self.active_clients = Dict[str, AutoBuildClient] = {}

    async def connect(self, client_id: str, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[get_cache_key(client_id, chat_id)] = websocket

    async def accept_client(self, client_id: str, chat_client: AutoBuildClient, websocket: WebSocket):
        await websocket.accept()
        self.active_clients[client_id] = chat_client

    def clear_client(self, client_id: str):
        if client_id not in self.active_clients:
            logger.error('close_client client_id={} not in active_clients', client_id)
            return
        logger.info('close_client client_id={}', client_id)
        self.active_clients.pop(client_id, None)

    async def close_client(self, client_id: str):
        if self.active_clients.get(client_id):
            chat_client = self.active_clients.get(client_id)
            try:
                await chat_client.websocket.close()
                self.clear_client(client_id)
            except Exception as err:
                if 'after sending' in str(err):
                    logger.error(str(err))

    async def control_auto_client(self, chat_id: str, login_user: UserPayload, websocket: WebSocket):

        client_id = uuid.uuid4().hex
        chat_client = AutoBuildClient(chat_id=chat_id,
                                      client_key=client_id,
                                      login_user=login_user,
                                      websocket=websocket)
        await self.accept_client(client_id, chat_client, websocket)

        try:
            await chat_client.run_chat()
        except WebSocketDisconnect as err:
            logger.info('act=rcv_client_disconnect {}', str(err))
        except Exception as err:
            # Handle any exceptions that might occur
            logger.exception(str(err))
            await self.close_client(client_id)
        finally:
            try:
                await self.close_client(client_id)
            except Exception as err:
                logger.exception(err)
            self.clear_client(client_id)
