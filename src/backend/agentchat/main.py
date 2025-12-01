from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agentchat.middleware.trace_id_middleware import TraceIDMiddleware
from agentchat.middleware.white_list_middleware import WhitelistMiddleware
from agentchat.settings import initialize_app_settings
from agentchat.settings import app_settings

import warnings
warnings.filterwarnings("ignore")

async def register_router(app: FastAPI):
    from agentchat.api.router import router

    app.include_router(router)

    # 健康探针
    @app.get("/health")
    def check_health():
        return {'status': 'OK'}


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

    # Trace ID的中间件操作
    app.add_middleware(TraceIDMiddleware)

    # 注册白名单中间件
    app.add_middleware(WhitelistMiddleware)


    return app


async def init_config():
    await initialize_app_settings()

    # 必须放到init settings 之后 import
    from agentchat.database.init_data import init_database, init_default_agent, update_system_mcp_server
    await init_database()
    await init_default_agent()
    await update_system_mcp_server()

def print_logo():
    from pyfiglet import Figlet

    f = Figlet(font="slant")
    print(f.renderText("Agent Chat"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前执行
    await init_config()
    await register_router(app)
    print_logo()
    yield
    # 关闭时执行
    # pass


def create_app():
    app = FastAPI(title=app_settings.server.get("project_name", "AgentChat"),
                  version=app_settings.server.get("version", "v2.2.0"),
                  lifespan=lifespan)

    app = register_middleware(app)

    from agentchat.api.JWT import Settings

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

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agentchat.main:app", host="0.0.0.0", port=7860)
