from fastapi import APIRouter, Request
from agentchat.api.services.message import MessageLikeService, MessageDownService
from agentchat.schema.schemas import resp_200

router = APIRouter(tags=["Message"])


@router.post("/message/like")
async def insert_message_like(request: Request):
    body = await request.json()

    user_input = body.get('user_input')
    agent_output = body.get('agent_output')
    MessageLikeService.create_message_like(user_input=user_input,
                                           agent_output=agent_output)

    return resp_200()


@router.post("/message/down")
async def insert_message_down(request: Request):
    body = await request.json()

    user_input = body.get('user_input')
    agent_output = body.get('agent_output')
    MessageDownService.create_message_down(user_input=user_input,
                                           agent_output=agent_output)

    return resp_200()


# @router.get("/config", description="获取用户配置")
# async def get_user_config():
#     try:
#         return resp_200(data=userConfig.get_user_config())
#     except Exception as err:
#         logger.error(f"get user config API error: {err}")
#         return resp_500(data=get_user_config_error)
#
#
# @router.post("/config", description="修改用户配置")
# async def update_user_config(data: str = Form(...)):
#     try:
#         userConfig.update_yaml_file(data)
#         userConfig.reload_config()
#     except Exception as err:
#         logger.error(f"update user config API error: {err}")
#         return resp_500(data=update_user_config_error)
