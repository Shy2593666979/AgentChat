from agentchat.database.models.llm import LLMTable
from agentchat.database.models.user import AdminUser, SystemUser
from agentchat.schema.schemas import UnifiedResponseModel, resp_500, resp_200
from agentchat.database.dao.llm import LLMDao
from loguru import logger

LLM_Types = ['LLM', 'Embedding', 'Reranker']


class LLMService:

    @classmethod
    async def create_llm(cls, user_id: str, api_key: str, model: str,
                         base_url: str, provider: str, llm_type: str):
        try:
            await LLMDao.create_llm(base_url=base_url, api_key=api_key,
                                    model=model, provider=provider, user_id=user_id, llm_type=llm_type)
        except Exception as err:
            raise ValueError(f'Create LLM Appear Err: {err}')

    @classmethod
    async def delete_llm(cls, llm_id: str):
        try:
            await LLMDao.delete_llm(llm_id=llm_id)
        except Exception as err:
            raise ValueError(f'Delete LLM Appear Err: {err}')

    @classmethod
    async def verify_user_permission(cls, llm_id, user_id):
        if user_id == AdminUser or user_id == await cls.get_user_id_by_llm(llm_id):
            pass
        else:
            raise ValueError(f"没有权限访问")

    @classmethod
    async def get_user_id_by_llm(cls, llm_id: str):
        try:
            llm = await LLMDao.get_user_id_by_llm(llm_id)
            return llm.user_id
        except Exception as err:
            raise ValueError(f'Get User Id By LLM Appear Err: {err}')

    @classmethod
    async def update_llm(cls, llm_id: str, model: str, base_url: str, api_key: str, provider: str, llm_type: str):
        try:
            await LLMDao.update_llm(llm_id=llm_id, model=model, llm_type=llm_type,
                                    base_url=base_url, api_key=api_key, provider=provider)
        except Exception as err:
            raise ValueError(f'Update LLM Appear Err: {err}')

    @classmethod
    async def get_personal_llm(cls, user_id: str):
        try:
            llm_data = await LLMDao.get_llm_by_user(user_id)
            result = []
            for data in llm_data:
                result.append(data.to_dict())
            # 按照LLM的种类进行单独返回数据
            resp_llm = {}
            for llm_type in LLM_Types:
                resp_llm[llm_type] = []
            for res in result:
                # 针对官网的API KEY进行隐藏
                if res["user_id"] == SystemUser:
                    res["api_key"] = "************"
                resp_llm[res["llm_type"]].append(res)

            return resp_llm
        except Exception as err:
            raise ValueError(f'Get Personal LLM Appear Err: {err}')

    @classmethod
    async def get_visible_llm(cls, user_id: str):
        try:
            user_data = await LLMDao.get_llm_by_user(user_id)
            system_data = await LLMDao.get_llm_by_user(SystemUser)
            result = []
            for data in (user_data + system_data):
                result.append(data.to_dict())
            # 按照LLM的种类进行单独返回数据
            resp_llm = {}
            for llm_type in LLM_Types:
                resp_llm[llm_type] = []
            for res in result:
                # 针对官网的API KEY进行隐藏
                if res["user_id"] == SystemUser:
                    res["api_key"] = "************"
                resp_llm[res["llm_type"]].append(res)

            return resp_llm
        except Exception as err:
            raise ValueError(f'Get Visible LLM Appear Err: {err}')

    @classmethod
    async def get_all_llm(cls, user_id: str = None):
        try:
            llm_data = await LLMDao.get_all_llm()
            result = []
            for data in llm_data:
                result.append(data.to_dict())
            # 按照LLM的种类进行单独返回数据
            resp_llm = {}
            for llm_type in LLM_Types:
                resp_llm[llm_type] = []
            for res in result:
                res["api_key"] = "************"
                resp_llm[res["llm_type"]].append(res)

            return resp_llm
        except Exception as err:
            raise ValueError(f'Get All LLM Appear Err: {err}')

    @classmethod
    async def get_llm_by_id(cls, llm_id: str):
        try:
            llms = await LLMDao.get_llm_by_id(llm_id)
            return llms.to_dict()
        except Exception as err:
            raise ValueError(f'Get LLM By Id Appear Err: {err}')

    @classmethod
    async def get_one_llm(cls):
        try:
            llms = await LLMDao.get_all_llm()
            return llms[0].to_dict()
        except Exception as err:
            raise ValueError(f'Get One LLM Appear Err: {err}')

    @classmethod
    async def get_llm_type(cls):
        try:
            llms = await LLMDao.get_llm_by_type(llm_type='LLM')
            return [llm.to_dict() for llm in llms]
        except Exception as err:
            raise ValueError(f'Get LLM Type Appear Err: {err}')

    @classmethod
    async def get_llm_id_from_name(cls, llm_name, user_id):
        try:
            llm = await LLMDao.get_llm_id_from_name(llm_name, user_id)
            if llm:
                return llm.llm_id
            else:
                llm = await LLMDao.get_llm_id_from_name(llm_name, SystemUser)
                return llm.llm_id
        except Exception as err:
            raise ValueError(f'Get LLM ID Err: {err}')



# 2024-630---->2025-630版本（已退休）❌

# Function_Call_provider = ['OpenAI', 'Anthropic', 'Gemini', 'Mistral', 'DeepSeek', '智谱AI']
#
# React_provider = ['百度智能', '通义千问', '腾讯混元', '百川智能', '豆包', '零一万物', '科大讯飞']
# class LLMService:
#
#     @classmethod
#     def create_llm(cls, user_id: str, api_key: str, model: str,
#                    base_url: str, provider: str, llm_type: str):
#         try:
#             LLMDao.create_llm(base_url=base_url, api_key=api_key,
#                               model=model, provider=provider, user_id=user_id, llm_type=llm_type)
#             return resp_200()
#         except Exception as err:
#             logger.error(f'create llm appear Err: {err}')
#             return resp_500()
#
#     @classmethod
#     def delete_llm(cls, user_id: str, llm_id: str):
#         try:
#             if user_id == AdminUser or  user_id == cls.get_user_id_by_llm(llm_id):
#                 LLMDao.delete_llm(llm_id=llm_id)
#                 return resp_200()
#             else:
#                 logger.error(f'no permission exec')
#                 return resp_500()
#         except Exception as err:
#             logger.error(f'delete llm appear Err: {err}')
#             return resp_500()
#
#
#     @classmethod
#     def get_user_id_by_llm(cls, llm_id: str):
#         try:
#             llm = LLMDao.get_user_id_by_llm(llm_id)
#             return llm[0].user_id
#         except Exception as err:
#             logger.error(f'get user id by llm appear Err: {err}')
#             return str(err)
#
#     @classmethod
#     def update_llm(cls, user_id: str, llm_id: str, model: str,
#                    base_url: str, api_key: str, provider: str, llm_type: str):
#         try:
#             if user_id == AdminUser or user_id == cls.get_user_id_by_llm(llm_id):
#                 LLMDao.update_llm(llm_id=llm_id, model=model, llm_type=llm_type,
#                                   base_url=base_url, api_key=api_key, provider=provider)
#                 return resp_200()
#             else:
#                 logger.error(f'no permission exec')
#                 return resp_500()
#         except Exception as err:
#             logger.error(f'update llm appear Err: {err}')
#             return resp_500()
#
#     @classmethod
#     def get_personal_llm(cls, user_id: str):
#         try:
#             llm_data = LLMDao.get_llm_by_user(user_id)
#             result = []
#             for data in llm_data:
#                 result.append(data[0])
#             # 按照LLM的种类进行单独返回数据
#             resp_llm = {}
#             for llm_type in LLM_Types:
#                 resp_llm[llm_type] = []
#             for res in result:
#                 resp_llm[res.llm_type].append(res)
#
#             return resp_200(data=resp_llm)
#         except Exception as err:
#             logger.error(f'get personal llm appear Err: {err}')
#             return resp_500()
#
#     @classmethod
#     def get_visible_llm(cls, user_id: str):
#         try:
#             user_data = LLMDao.get_llm_by_user(user_id)
#             system_data = LLMDao.get_llm_by_user(SystemUser)
#             result = []
#             for data in (user_data + system_data):
#                 result.append(data[0])
#             # 按照LLM的种类进行单独返回数据
#             resp_llm = {}
#             for llm_type in LLM_Types:
#                 resp_llm[llm_type] = []
#             for res in result:
#                 resp_llm[res.llm_type].append(res)
#
#             return resp_200(data=resp_llm)
#         except Exception as err:
#             logger.error(f'get visible llm appear Err: {err}')
#             return resp_500()
#
#     @classmethod
#     def get_all_llm(cls):
#         try:
#             llm_data = LLMDao.get_all_llm()
#             result = []
#             for data in llm_data:
#                 result.append(data[0])
#             # 按照LLM的种类进行单独返回数据
#             resp_llm = {}
#             for llm_type in LLM_Types:
#                 resp_llm[llm_type] = []
#             for res in result:
#                 resp_llm[res.llm_type].append(res)
#
#             return resp_200(data=resp_llm)
#         except Exception as err:
#             logger.error(f'get all llm appear Err: {err}')
#             return resp_500()
#
#     @classmethod
#     def get_llm_by_id(cls, llm_id: str):
#         try:
#             llm = LLMDao.get_llm_by_id(llm_id)
#             return llm
#         except Exception as err:
#             logger.error(f'get llm by id appear Err: {err}')
#
#     @classmethod
#     def get_one_llm(cls):
#         try:
#             llm = LLMDao.get_all_llm()
#             return llm[0][0]
#         except Exception as err:
#             logger.error(f'get one llm appear Err: {err}')
#
#     @classmethod
#     def get_llm_type(cls):
#         try:
#             llms = LLMDao.get_llm_by_type(llm_type='LLM')
#             result = []
#             for llm in llms:
#                 result.append(llm[0])
#             return result
#         except Exception as err:
#             logger.error(f'get llm type appear Err: {err}')
#
