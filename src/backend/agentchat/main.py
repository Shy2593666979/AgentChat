from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentchat.api.JWT import Settings as AuthJwtSettings
from agentchat.auth import AuthJWT
from agentchat.auth.exceptions import AuthJWTException
from agentchat.mcp_proxy.session.manager import SessionManager
from agentchat.middleware.trace_id_middleware import TraceIDMiddleware
from agentchat.middleware.white_list_middleware import WhitelistMiddleware
from agentchat.settings import app_settings, init_app_settings
from agentchat.utils.logging import configure_logging


async def register_router(app: FastAPI):
    from agentchat.api.router import router

    app.include_router(router)

    # 健康探针
    @app.get("/health")
    def check_health():
        return {
            'status': 'OK',
        }


def register_middleware(app: FastAPI):
    origins = [
        '*',
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # 注册白名单中间件
    app.add_middleware(WhitelistMiddleware)

    # 日志中间件放在最外层，覆盖真实响应发送和客户端断开。
    app.add_middleware(TraceIDMiddleware)

    return app


async def init_config():
    await init_app_settings()
    configure_logging(app_settings.log_level, secrets=app_settings.dict())

    from agentchat.database.init_data import init_agentchat_system
    await init_agentchat_system()

def print_logo():
    from pyfiglet import Figlet

    f = Figlet(font="slant")
    print(f.renderText("Agent Chat"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_config()

    endpoint = app_settings.redis.get("endpoint")
    redis_client = aioredis.from_url(endpoint, decode_responses=True) if endpoint else None
    app.state.session_manager = SessionManager(redis_client)

    if app_settings.storage.mode == "local":
        from fastapi.staticfiles import StaticFiles

        from agentchat.services.storage import storage_client
        # 上传文件与现有对象存储一样通过 URL 访问。
        app.mount("/uploads", StaticFiles(directory=str(storage_client.root)), name="uploads")

    await register_router(app)
    from agentchat.api.services.conversation import ConversationService
    from agentchat.services.mcp.metadata import stop_metadata_tasks
    print_logo()

    yield

    await stop_metadata_tasks()
    await ConversationService.stop_conversation_title_tasks()
    if redis_client is not None:
        await redis_client.close()


def create_app():
    configure_logging(app_settings.log_level)
    app = FastAPI(
        title=app_settings.server.name,
        version=app_settings.server.version,
        lifespan=lifespan
    )

    app = register_middleware(app)

    # 配置 AuthJWT
    @AuthJWT.load_config
    def get_config():
        return AuthJwtSettings()

    # 处理 AuthJWT 异常
    @app.exception_handler(AuthJWTException)
    def authjwt_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
            },
        )

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentchat.main:app", host="0.0.0.0", port=7860)
