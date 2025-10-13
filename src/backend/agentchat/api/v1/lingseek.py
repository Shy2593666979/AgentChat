from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.schema.lingseek import LingSeekGuidePrompt, LingSeekGuidePromptFeedBack, LingSeekTask
from agentchat.services.lingseek.agent import LingSeekAgent

router = APIRouter(prefix="/workbench/lingseek")

@router.post("/guide_prompt", summary="生成灵寻的指导提示")
async def generate_lingseek_guide_prompt(*,
                                         lingseek_info: LingSeekGuidePrompt,
                                         login_user: UserPayload = Depends(get_login_user)):
    lingseek_agent = LingSeekAgent()
    async def general_generate():
        async for chunk in lingseek_agent.generate_guide_prompt(lingseek_info):
            yield chunk

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/guide_prompt/feedback", summary="根据用户的反馈进行重新生成")
async def rebuild_generate_lingseek_guide_prompt(*,
                                                 feedback_guide_prompt: LingSeekGuidePromptFeedBack,
                                                 login_user: UserPayload = Depends(get_login_user)):
    lingseek_agent = LingSeekAgent()
    async def general_generate():
        async for chunk in lingseek_agent.generate_guide_prompt(feedback_guide_prompt, True):
            yield chunk

    return StreamingResponse(general_generate(), media_type="text/event-stream")

@router.post("/task", summary="灵寻生成的任务列表")
async def generate_lingseek_tasks(*,
                                  task: LingSeekTask,
                                  login_user: UserPayload = Depends(get_login_user)):

    lingseek_agent = LingSeekAgent()
    async def general_generate():
        async for chunk in lingseek_agent.generate_tasks(task):
            yield chunk

    return StreamingResponse(general_generate(), media_type="text/event-stream")