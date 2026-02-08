from loguru import logger
from fastapi import APIRouter, Depends, Body

from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.common import CreateLLMRequest, UpdateLLMRequest
from agentchat.schema.schemas import UnifiedResponseModel, resp_200, resp_500
from agentchat.api.services.llm import LLMService, LLM_Types

router = APIRouter(tags=["LLM"])


@router.post("/llm/create", response_model=UnifiedResponseModel)
async def create_llm(
    *,
    llm_request: CreateLLMRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.create_llm(
            user_id=login_user.user_id,
            **llm_request.model_dump()
        )
        return resp_200()
    except Exception as err:
        logger.exception("Create LLM failed")
        return resp_500(message=str(err))


@router.delete("/llm/delete", response_model=UnifiedResponseModel)
async def delete_llm(
    llm_id: str = Body(..., embed=True, description="大模型的ID"),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.verify_user_permission(
            llm_id=llm_id,
            user_id=login_user.user_id
        )
        await LLMService.delete_llm(llm_id)
        return resp_200()
    except Exception as err:
        logger.exception("Delete LLM failed")
        return resp_500(message=str(err))


@router.put("/llm/update", response_model=UnifiedResponseModel)
async def update_llm(
    *,
    llm_request: UpdateLLMRequest,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.verify_user_permission(
            llm_id=llm_request.llm_id,
            user_id=login_user.user_id
        )
        await LLMService.update_llm(**llm_request.model_dump())
        return resp_200()
    except Exception as err:
        logger.exception("Update LLM failed")
        return resp_500(message=str(err))


@router.get("/llm/all", response_model=UnifiedResponseModel)
async def get_all_llm(login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await LLMService.get_all_llm()
        return resp_200(data=result)
    except Exception as err:
        logger.exception("Get all LLM failed")
        return resp_500(message=str(err))


@router.post("/llm/personal", response_model=UnifiedResponseModel)
async def get_personal_llm(login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await LLMService.get_personal_llm(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        logger.exception("Get personal LLM failed")
        return resp_500(message=str(err))


@router.post("/llm/visible", response_model=UnifiedResponseModel)
async def get_visible_llm(login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await LLMService.get_visible_llm(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        logger.exception("Get visible LLM failed")
        return resp_500(message=str(err))


@router.get("/agent/models", response_model=UnifiedResponseModel)
async def get_all_agent_models(login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await LLMService.get_visible_llm(login_user.user_id)
        return resp_200(data=result.get("LLM", []))
    except Exception as err:
        logger.exception("Get agent models failed")
        return resp_500(message=str(err))


@router.get("/llm/schema", response_model=UnifiedResponseModel)
async def get_llm_type(login_user: UserPayload = Depends(get_login_user)):
    return resp_200(data=LLM_Types)
