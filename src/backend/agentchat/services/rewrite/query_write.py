import json

from loguru import logger
from agentchat.core.models.models import AsyncChatClient
from agentchat.settings import app_settings
from agentchat.prompts.system import system_query_rewrite
from agentchat.prompts.user import user_query_write

class QueryRewrite:
    def __init__(self):
        self.client = AsyncChatClient(model_name=app_settings.multi_models.qwen2.model_name,
                                      api_key=app_settings.multi_models.qwen2.api_key,
                                      base_url=app_settings.multi_models.qwen2.base_url)

    async def rewrite(self, user_input):
        rewrite_prompt = user_query_write.format(user_input=user_input)
        response = await self.client.ainvoke(rewrite_prompt, system_query_rewrite)
        cleaned_response = response.replace("```json", "")
        cleaned_response = cleaned_response.replace("```", "").strip()

        try:
            result = json.loads(cleaned_response)
            return result
        except Exception as e:
            logger.info(f"json loads error: {e}")
            return [user_input]

query_rewriter = QueryRewrite()