from loguru import logger
from agentchat.database.dao.llm import LLMDao
from agentchat.database.models.user import AdminUser, SystemUser

LLM_Types = ['LLM', 'Embedding', 'Reranker']


class LLMService:

    @classmethod
    async def create_llm(cls, **kwargs):
        await LLMDao.create_llm(**kwargs)

    @classmethod
    async def delete_llm(cls, llm_id: str):
        await LLMDao.delete_llm(llm_id)

    @classmethod
    async def verify_user_permission(cls, llm_id: str, user_id: str):
        owner_id = await cls.get_user_id_by_llm(llm_id)
        if user_id not in (AdminUser, owner_id):
            raise ValueError("没有权限访问")

    @classmethod
    async def get_user_id_by_llm(cls, llm_id: str):
        llm = await LLMDao.get_user_id_by_llm(llm_id)
        return llm.user_id

    @classmethod
    async def update_llm(cls, **kwargs):
        await LLMDao.update_llm(**kwargs)

    @staticmethod
    def _group_by_type(llms: list, hide_api_key: bool = False):
        resp = {t: [] for t in LLM_Types}
        for item in llms:
            if hide_api_key:
                item["api_key"] = "************"
            resp[item["llm_type"]].append(item)
        return resp

    @classmethod
    async def get_personal_llm(cls, user_id: str):
        llms = await LLMDao.get_llm_by_user(user_id)
        result = [llm.to_dict() for llm in llms]

        for r in result:
            if r["user_id"] == SystemUser:
                r["api_key"] = "************"

        return cls._group_by_type(result)

    @classmethod
    async def get_visible_llm(cls, user_id: str):
        user_llms = await LLMDao.get_llm_by_user(user_id)
        system_llms = await LLMDao.get_llm_by_user(SystemUser)

        result = [llm.to_dict() for llm in (user_llms + system_llms)]
        for r in result:
            if r["user_id"] == SystemUser:
                r["api_key"] = "************"

        return cls._group_by_type(result)

    @classmethod
    async def get_all_llm(cls):
        llms = await LLMDao.get_all_llm()
        result = [llm.to_dict() for llm in llms]
        return cls._group_by_type(result, hide_api_key=True)

    @classmethod
    async def get_llm_by_id(cls, llm_id: str):
        llm = await LLMDao.get_llm_by_id(llm_id)
        return llm.to_dict() if llm else None

    @classmethod
    async def get_one_llm(cls):
        llms = await LLMDao.get_all_llm()
        return llms[0].to_dict() if llms else None

    @classmethod
    async def get_llm_type(cls):
        llms = await LLMDao.get_llm_by_type('LLM')
        return [llm.to_dict() for llm in llms]

    @classmethod
    async def get_llm_id_from_name(cls, llm_name: str, user_id: str):
        llm = await LLMDao.get_llm_id_from_name(llm_name, user_id)
        if llm:
            return llm.llm_id
        llm = await LLMDao.get_llm_id_from_name(llm_name, SystemUser)
        return llm.llm_id if llm else None
