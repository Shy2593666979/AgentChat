from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agentchat.settings import initialize_app_settings
from agentchat.settings import app_settings


async def register_router(app: FastAPI):
    from agentchat.api.router import router
    app.mount("/img", StaticFiles(directory="agentchat/data/img"), name="img")
    app.include_router(router)


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

    # 全局中间件：标记白名单请求
    @app.middleware("http")
    def mark_whitelist_paths(request: Request, call_next):
        # 检查请求路径是否以任何白名单前缀开头
        request.state.is_whitelisted = any(
            request.url.path.startswith(prefix) for prefix in app_settings.whitelist_paths
        )
        # 检查请求路径以具体白名单匹配
        # request.state.is_whitelisted = request.url.path in app_settings.whitelist_paths
        return call_next(request)

    return app


async def init_config():
    await initialize_app_settings()

    # 必须放到init settings 之后 import
    from agentchat.database.init_data import init_database, init_default_agent, update_system_mcp_server
    await init_database()
    await init_default_agent()
    await update_system_mcp_server()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前执行
    await init_config()
    await register_router(app)
    yield
    # 关闭时执行
    # pass


def create_app():
    app = FastAPI(title=app_settings.server.get('project_name') or "AgentChat",
                  version=app_settings.server.get('version') or "V2025.630",
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


app = create_app()  # 不需要使用 await


def main():
    import uvicorn
    uvicorn.run("main:app",
                host=app_settings.server.get('host'),
                port=app_settings.server.get('port'))


if __name__ == "__main__":
    main()

# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from fastapi_jwt_auth import AuthJWT
# from fastapi_jwt_auth.exceptions import AuthJWTException
# from fastapi.responses import JSONResponse
#
# from fastapi.middleware.cors import CORSMiddleware
#
#
# from agentchat.settings import initialize_app_settings
# from agentchat.settings import app_settings
#
#
# def register_router(app: FastAPI):
#     from agentchat.api.router import router
#     app.mount("/img", StaticFiles(directory="agentchat/data/img"), name="img")
#     app.include_router(router)
#
#
# def register_middleware(app: FastAPI):
#     origins = [
#         '*',
#     ]
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=origins,
#         allow_credentials=False,
#         allow_methods=['*'],
#         allow_headers=['*'],
#     )
#
#     return app
#
# def init_config():
#     initialize_app_settings()
#
#     # 必须放到init settings 之后 import
#     from agentchat.database.init_data import init_database, init_default_agent
#     init_database()
#     init_default_agent()
#
# def create_app():
#     init_config()
#
#     app = FastAPI(title=app_settings.server.get('project_name'),
#                   version=app_settings.server.get('version'))
#
#     from agentchat.api.JWT import Settings
#
#     register_router(app)
#     register_middleware(app)
#
#     # 配置 AuthJWT
#     @AuthJWT.load_config
#     def get_config():
#         return Settings()
#
#     # 处理 AuthJWT 异常
#     @app.exception_handler(AuthJWTException)
#     def authjwt_exception_handler(request, exc):
#         return JSONResponse(
#             status_code=exc.status_code,
#             content={"detail": exc.message}
#         )
#
#     return app
#
# app = create_app()
#
# def main():
#     import uvicorn
#     uvicorn.run("main:app",
#                 host=app_settings.server.get('host'),
#                 port=app_settings.server.get('port'))
#
# if  __name__ == "__main__":
#     main()
