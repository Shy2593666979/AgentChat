from fastapi import APIRouter, Request, Form
from service.message import MessageLikeService, MessageDownService
from config.user_config import userConfig
from type.schemas import resp_200, resp_500
from prompt.resp_template import update_user_config_error, get_user_config_error
from loguru import logger

router = APIRouter()


@router.post("/message/like")
async def insert_message_like(request: Request):
    body = await request.json()

    userInput = body.get('userInput')
    agentOutput = body.get('agentOutput')
    MessageLikeService.create_message_like(userInput=userInput,
                                           agentOutput=agentOutput)

    return resp_200()


@router.post("/message/down")
async def insert_message_down(request: Request):
    body = await request.json()

    userInput = body.get('userInput')
    agentOutput = body.get('agentOutput')
    MessageDownService.create_message_down(userInput=userInput,
                                           agentOutput=agentOutput)

    return resp_200()


@router.get("/config", description="获取用户配置")
async def get_user_config():
    try:
        return resp_200(data=userConfig.get_user_config())
    except Exception as err:
        logger.error(f"get user config API error: {err}")
        return resp_500(data=get_user_config_error)


@router.post("/config", description="修改用户配置")
async def update_user_config(data: str = Form(...)):
    try:
        userConfig.update_yaml_file(data)
        userConfig.reload_config()
    except Exception as err:
        logger.error(f"update user config API error: {err}")
        return resp_500(data=update_user_config_error)
