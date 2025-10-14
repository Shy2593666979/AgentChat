from agentchat.core.models.manager import ModelManager


class WorkSpacePublicAgent:

    def __init__(self, model_config, enable_search):
        self.model = ModelManager.get_user_model(**model_config)
        self.enable_search = enable_search

    async def ainvoke(self):
        pass

    async def astream(self):
        pass