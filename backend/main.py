from typing import List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from pydantic import BaseSettings

from database.init_data import  init_database, init_default_agent
from fastapi.middleware.cors import CORSMiddleware
from config.service_config import SERVICE_HOST, SERVICE_PORT
from routers import chat, dialog, message, agent, history, tool, user, llm
from config.user_config import userConfig

app = FastAPI()

# 允许所有来源的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/img", StaticFiles(directory="img"), name="img")

app.include_router(chat.router, prefix="/api")
app.include_router(dialog.router, prefix="/api")
app.include_router(message.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(tool.router, prefix="/api")
app.include_router(llm.router, prefix="/api")

# 定义 Pydantic 的 BaseSettings 类
class Settings(BaseSettings):
    authjwt_secret_key: str = 'secret'
    authjwt_token_location: list = ['cookies', 'headers']
    authjwt_cookie_csrf_protect: bool = False

# 配置 AuthJWT
@AuthJWT.load_config
def get_config():
    return Settings()

# 处理 AuthJWT 异常
@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


if  __name__ == "__main__":
    init_database()
    init_default_agent()

    uvicorn.run("main:app", host=SERVICE_HOST, port=SERVICE_PORT)