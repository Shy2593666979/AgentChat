import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from database import  init_database, init_default_agent
from fastapi.middleware.cors import CORSMiddleware
from config.service_config import SERVICE_HOST, SERVICE_PORT
from routers import chat, dialog, message

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

app.include_router(chat.router)
app.include_router(dialog.router)
app.include_router(message.router)

if  __name__ == "__main__":
    init_database()
    init_default_agent()
    uvicorn.run("main:app", host=SERVICE_HOST, port=SERVICE_PORT)