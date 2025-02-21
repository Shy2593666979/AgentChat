import json

from loguru import logger
from core.models import AsyncChatClient
from settings import app_settings
from prompts.system import system_query_rewrite
from prompts.user import user_query_write

class QueryRewrite:
    def __init__(self):
        self.client = AsyncChatClient(model_name=app_settings.llm.get('model_name'),
                                      base_url=app_settings.llm.get('base_url'),
                                      api_key=app_settings.llm.get('api_key'))

    async def rewrite(self, user_input):
        rewrite_prompt = user_query_write.format(user_input=user_input)
        response = self.client.ainvoke(rewrite_prompt, system_query_rewrite)
        cleaned_response = response.replace("```json", "")
        cleaned_response = cleaned_response.replace("```", "").strip()

        try:
            result = json.loads(cleaned_response)
            return result
        except Exception as e:
            logger.info(f"json loads error: {e}")
            return []