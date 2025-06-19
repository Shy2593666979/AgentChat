import sys

sys.path.append("..")
from config import update_system_config
from src.backend import config

update_system_config()

print(config.LLM_OPENAI_API_KEY)
print(config.LLM_OPENAI_BASE_URL)
