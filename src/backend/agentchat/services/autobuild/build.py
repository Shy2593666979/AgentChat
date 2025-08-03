import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketException
from fastapi import status as http_status
from fastapi_jwt_auth import AuthJWT
from loguru import logger

from agentchat.services.autobuild.manager import AutoBuildManager
from agentchat.api.services.user import UserPayload

router = APIRouter()


@router.websocket('/build/auto')
async def chat(websocket: WebSocket,
               chat_id: Optional[str] = None,
               Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required(auth_from='websocket', websocket=websocket)

        payload = Authorize.get_jwt_subject()
        if not isinstance(payload, str):
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT payload")
        payload = json.loads(payload)

        login_user = UserPayload(**payload)
        chat_manager = AutoBuildManager()
        await chat_manager.control_auto_client(login_user=login_user, websocket=websocket, chat_id=chat_id or "")

    except WebSocketException as exc:
        logger.exception(f'Websocket exception: {str(exc)}')
        await websocket.close(code=http_status.WS_1011_INTERNAL_ERROR, reason=str(exc))
    except Exception as exc:
        logger.exception(f'Error in chat websocket: {str(exc)}')
        message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        if 'Could not validate credentials' in str(exc):
            await websocket.close(code=http_status.WS_1008_POLICY_VIOLATION, reason='Unauthorized')
        else:
            await websocket.close(code=http_status.WS_1011_INTERNAL_ERROR, reason=message)
