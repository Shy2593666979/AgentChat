from fastapi import APIRouter, Depends, HTTPException

from agentchat.api.services.user import get_login_user, UserPayload
from agentchat.schema.llm import LLMUpdateReq, LLMCreateReq, LLMDeleteReq, LLMSearchReq
from agentchat.schema.schemas import resp_200, resp_500
from agentchat.api.services.llm import LLMService, LLM_Types

router = APIRouter(tags=["LLM"], prefix="/llm")


@router.post("/create", summary="用户进行创建模型")
async def create_llm(
    req: LLMCreateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.create_llm(
            user_id=login_user.user_id,
            **req.model_dump()
        )
        return resp_200()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.delete("/delete", summary="用户删除自己的模型")
async def delete_llm(
    req: LLMDeleteReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.verify_user_permission(
            llm_id=req.llm_id,
            user_id=login_user.user_id
        )
        await LLMService.delete_llm(req.llm_id)
        return resp_200()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.put("/update", summary="用户更新模型")
async def update_llm(
    req: LLMUpdateReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.verify_user_permission(
            llm_id=req.llm_id,
            user_id=login_user.user_id
        )
        await LLMService.update_llm(**req.model_dump())
        return resp_200()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/all", summary="获得所有的模型列表")
async def get_all_llm(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await LLMService.get_all_llm(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/personal", summary="获取用户仅自己创建的模型")
async def get_personal_llm(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await LLMService.get_personal_llm(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/visible", summary="获取用户仅自己可见的模型")
async def get_visible_llm(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await LLMService.get_visible_llm(login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/agent/models", summary="获取Agent中可用的模型")
async def get_all_agent_models(
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await LLMService.get_visible_llm(login_user.user_id)
        return resp_200(data=result.get("LLM", []))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@router.post("/search", summary="根据用户名称进行搜索模型")
async def search_models(
    req: LLMSearchReq,
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        result = await LLMService.search_llms_by_name(login_user.user_id, req.llm_name)
        return resp_200({"LLM": result})
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/schema", summary="模型格式")
async def get_llm_type(
    login_user: UserPayload = Depends(get_login_user)
):
    return resp_200(data=LLM_Types)
