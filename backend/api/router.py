from fastapi import APIRouter
from api.v1 import chat, dialog, message, agent, history, user, llm, tool

router = APIRouter(prefix="/api/v1")

router.include_router(chat.router)
router.include_router(dialog.router)
router.include_router(message.router)
router.include_router(agent.router)
router.include_router(history.router)
router.include_router(user.router)
router.include_router(tool.router)
router.include_router(llm.router)