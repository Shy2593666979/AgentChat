from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse

from database.init_data import  init_database, init_default_agent
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, dialog, message, agent, history, tool, user, llm
from api.JWT import Settings
from settings import initialize_app_settings
from settings import app_settings


def register_router(app: FastAPI):
    app.mount("/img", StaticFiles(directory="img"), name="img")

    app.include_router(chat.router, prefix="/api")
    app.include_router(dialog.router, prefix="/api")
    app.include_router(message.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")
    app.include_router(history.router, prefix="/api")
    app.include_router(user.router, prefix="/api")
    app.include_router(tool.router, prefix="/api")
    app.include_router(llm.router, prefix="/api")

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

    return app

def init_config():
    initialize_app_settings()
    init_database()
    init_default_agent()

def create_app():
    app = FastAPI(title=app_settings.server.get('project_name'),
                  version=app_settings.server.get('version'))

    init_config()
    register_router(app)
    register_middleware(app)

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

def main():
    import uvicorn
    uvicorn.run("main:app",
                host=app_settings.server.get('host'),
                port=app_settings.server.get('port'))

if  __name__ == "__main__":
    main()
