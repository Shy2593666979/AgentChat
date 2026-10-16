from fastapi import APIRouter, Body, Depends
from loguru import logger

from agentchat.api.responses.builder import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.agent import AgentService
from agentchat.api.services.conversation import ConversationService
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schemas.conversation import (
    ConversationAgentUpdateRequest,
    ConversationCreateRequest,
)

router = APIRouter(tags=["Conversation"])


@router.get("/conversation/list", response_model=UnifiedResponseModel)
async def get_conversation(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        messages = await ConversationService.get_list_conversation(user_id=login_user.user_id)
        usage = await UsageStatsService.get_conversation_usage(login_user.user_id, [message["conversation_id"] for message in messages])
        results = []

        for message in messages:
            message_agent = await AgentService.select_agent_by_id(
                agent_id=message["agent_id"]
            )
            message_agent = message_agent or {}
            # 会话标题、归属和时间属于会话，不能被智能体信息覆盖。
            message["agent_name"] = message_agent.get("name", "")
            message.update(
                {
                    key: value
                    for key, value in message_agent.items()
                    if key not in message
                }
            )
            message["title_pending"] = ConversationService.conversation_title_pending(message["conversation_id"])
            message.update(
                usage.get(
                    message["conversation_id"],
                    {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "model_calls": 0,
                        "usage_available": False,
                    },
                )
            )
            results.append(message)

        return resp_200(data=results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.post("/conversation", response_model=UnifiedResponseModel)
async def create_conversation(
    conversation_req: ConversationCreateRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        conversation = await ConversationService.create_conversation(
            name=conversation_req.name,
            agent_id=conversation_req.agent_id,
            agent_type=conversation_req.agent_type,
            user_id=login_user.user_id
        )
        return resp_200(conversation)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/conversation", response_model=UnifiedResponseModel)
async def switch_conversation_agent(
    req: ConversationAgentUpdateRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        conversation = await ConversationService.switch_agent(req.conversation_id, req.agent_id, login_user.user_id)
        return resp_200(conversation)
    except Exception as error:
        return resp_500(message=str(error))


@router.delete("/conversation", response_model=UnifiedResponseModel)
async def delete_conversation(
    conversation_id: str = Body(description="对话ID", embed=True),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证用户权限
        await ConversationService.verify_user_permission(conversation_id, login_user.user_id)

        await ConversationService.delete_conversation(conversation_id=conversation_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
