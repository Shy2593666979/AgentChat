from fastapi import APIRouter, Depends, HTTPException

from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.schemas import resp_200
from agentchat.schema.usage_stats import UsageStatsRequest

router = APIRouter(tags=["Usage-Stats"])

@router.post("/usage", summary="根据不同的参数获取用量统计")
async def get_agentchat_usage(usage_stats: UsageStatsRequest,
                              login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await UsageStatsService.get_usage_by_agent_model(
            user_id=login_user.user_id,
            **usage_stats.model_dump()
        )
        return resp_200(
            data=result
        )

    except Exception as err:
        return HTTPException(status_code=500, detail=str(err))

@router.post("/usage_count", summary="统计每个Agent、Model统计次数")
async def get_agentchat_usage_count(usage_stats: UsageStatsRequest,
                                    login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await UsageStatsService.get_usage_count_by_agent_model(
            user_id=login_user.user_id,
            **usage_stats.model_dump()
        )
        return resp_200(
            data=result
        )

    except Exception as err:
        return HTTPException(status_code=500, detail=str(err))


@router.get("/usage/models_list", summary="获取用量统计的模型列表")
async def get_usage_models(login_user: UserPayload = Depends(get_login_user)):
    try:
        models = await UsageStatsService.get_usage_models(login_user.user_id)
        return resp_200(
            data=models
        )
    except Exception as err:
        return HTTPException(status_code=500, detail=str(err))

@router.get("/usage/agents_list", summary="获取用量统计的智能体列表")
async def get_usage_agents(login_user: UserPayload = Depends(get_login_user)):
    try:
        agents = await UsageStatsService.get_usage_agents(login_user.user_id)
        return resp_200(
            data=agents
        )
    except Exception as err:
        return HTTPException(status_code=500, detail=str(err))
