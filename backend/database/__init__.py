from sqlmodel import SQLModel, create_engine
from database.models.agent import AgentTable
from database.models.history import HistoryTable
from database.models.user import SystemUser

from config.service_config import MYSQL_URL, TOOL_OPENAI, LOGO_PREFIX

from dotenv import load_dotenv

# 加载本地的env
load_dotenv(override=True)

engine = create_engine(MYSQL_URL, connect_args={"charset": "utf8mb4"})

