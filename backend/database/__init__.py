from sqlmodel import SQLModel, create_engine
from database.models.agent import AgentTable
from database.models.history import HistoryTable
from database.models.user import SystemUser

from settings import app_settings

from dotenv import load_dotenv

# 加载本地的env
load_dotenv(override=True)

engine = create_engine(app_settings.mysql.get('endpoint'), connect_args={"charset": "utf8mb4"})

