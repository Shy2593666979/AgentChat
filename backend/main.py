from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware


from settings import initialize_app_settings
from settings import app_settings


def register_router(app: FastAPI):
    from api.router import router
    app.mount("/img", StaticFiles(directory="data/img"), name="img")
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

    return app

def init_config():
    initialize_app_settings()

    # 必须放到init settings 之后 import
    from database.init_data import init_database, init_default_agent
    init_database()
    init_default_agent()

def create_app():
    init_config()

    app = FastAPI(title=app_settings.server.get('project_name'),
                  version=app_settings.server.get('version'))

    from api.JWT import Settings

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
