# -------------------------------
# 该文件目前版本已弃用
# -------------------------------


# from typing import List
#
# from database.services import  HistoryService, DialogService, AgentService
# from database.services import MessageDownService, MessageLikeService
# from schema.message import  Message
# from loguru import  logger
#
# class HistoryMessage:
#
#     @classmethod
#     def create_history(cls, role: str, content: str, dialog_id: str):
#         try:
#             HistoryService.create_history(role, content, dialog_id)
#         except Exception as err:
#             logger.error(f"add history data appear error: {err}")
#
#     @classmethod
#     def select_history(cls, dialog_id: str, k: int = 6):
#         try:
#             result = HistoryService.select_history(dialog_id, k)
#             message_sql: List[Message] = []
#             for data in result:
#                 message_sql.append(Message(content=data[0].content, role=data[0].role))
#             return message_sql
#         except Exception as err:
#             logger.error(f"select history is appear error: {err}")
#
#     @classmethod
#     def get_dialog_history(cls, dialog_id: str):
#         try:
#             result = HistoryService.get_dialog_history(dialog_id)
#             message_sql: List[Message] = []
#             for data in result:
#                 message_sql.append(Message(content=data[0].content, role=data[0].role))
#             return message_sql
#         except Exception as err:
#             logger.error(f"get dialog history is appear error: {err}")
#
# class DialogChat:
#
#     @classmethod
#     def create_dialog(cls, name: str, agent: str):
#         try:
#             dialog_id = DialogService.create_dialog(name, agent)
#             return dialog_id
#         except Exception as err:
#             logger.error(f"add dialog is appear error: {err}")
#
#     @classmethod
#     def select_dialog(cls, dialog_id: str):
#         try:
#             data = DialogService.select_dialog(dialog_id)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"select dialog is appear error: {err}")
#
#     @classmethod
#     def get_list_dialog(cls):
#         try:
#             data = DialogService.get_list_dialog()
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"get list dialog is appear error: {err}")
#
#     @classmethod
#     def get_agent_by_dialog_id(cls, dialog_id: str):
#         try:
#             data = DialogService.get_agent_by_dialog_id(dialog_id)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"select dialog is appear error: {err}")
#
#     @classmethod
#     def update_dialog_time(cls, dialog_id: str):
#         try:
#             DialogService.update_dialog_time(dialog_id=dialog_id)
#         except Exception as err:
#             logger.error(f"update dialog create time appear error: {err}")
#
#     @classmethod
#     def delete_dialog(cls, dialog_id: str):
#         try:
#             DialogService.delete_dialog_by_id(dialog_id=dialog_id)
#             HistoryService.delete_history_by_dialog_id(dialog_id=dialog_id)
#         except Exception as err:
#             logger.error(f"delete dialog appear error: {err}")
#
#     @classmethod
#     def check_dialog_iscustom(cls, dialog_id: str):
#         try:
#             result = DialogService.check_dialog_iscustom(dialog_id=dialog_id)
#             for data in result:
#                 if data[0].is_custom:
#                     return True
#             return False
#         except Exception as err:
#             logger.error(f"check dialog is Custom appear error: {err}")
#
# class Agent:
#
#     @classmethod
#     def create_agent(cls, name: str, description: str, logo: str, parameter: str, schema: str="openai", code: str="", is_custom: bool=True):
#         try:
#             agentId = AgentService.create_agent(name=name,
#                                                 description=description,
#                                                 logo=logo,
#                                                 parameter=parameter,
#                                                 schema=schema,
#                                                 code=code,
#                                                 is_custom=is_custom)
#             return agentId
#         except Exception as err:
#             logger.error(f"create agent is appear error: {err}")
#
#     @classmethod
#     def get_agent(cls):
#         try:
#             data = AgentService.get_agent()
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"get agent is appear error: {err}")
#
#
#     @classmethod
#     def select_agent_by_type(cls, schema: str):
#         try:
#             data = AgentService.select_agent_by_type(schema)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"select agent by schema is appear error: {err}")
#
#     @classmethod
#     def select_agent_by_custom(cls, is_custom):
#         try:
#             data = AgentService.select_agent_by_custom(is_custom=is_custom)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"select agent by custom is appear error: {err}")
#
#     @classmethod
#     def select_agent_by_name(cls, name: str):
#         try:
#             data = AgentService.select_agent_by_name(name)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"select agent by name is appear error: {err}")
#
#     @classmethod
#     def get_parameter_by_name(cls, name: str):
#         try:
#             data = AgentService.select_agent_by_name(name)
#             return data[0][0].parameter
#         except Exception as err:
#             logger.error(f"get parameter by name is appear error: {err}")
#
#     @classmethod
#     def get_code_by_name(cls, name: str):
#         try:
#             data = AgentService.select_agent_by_name(name)
#             return data[0][0].code
#         except Exception as err:
#             logger.error(f"get code by name is appear error: {err}")
#
#     @classmethod
#     def get_agent_by_name_type(cls, name: str, schema: str="openai"):
#         try:
#             data = AgentService.get_agent_by_name_type(name=name, schema=schema)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"get agent by name and schema appear error: {err}")
#
#     @classmethod
#     def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, code: str):
#         try:
#             AgentService.update_agent_by_id(id=id,
#                                             name=name,
#                                             logo=logo,
#                                             description=description,
#                                             parameter=parameter,
#                                             code=code)
#         except Exception as err:
#             logger.error(f"update agent by id appear error: {err}")
#
#     @classmethod
#     def delete_agent_by_id(cls, id: str):
#         try:
#             AgentService.delete_agent_by_id(id=id)
#         except Exception as err:
#             logger.error(f"delete agent by id appear: {err}")
#
#     @classmethod
#     def search_agent_name(cls, name: str):
#         try:
#             data = AgentService.search_agent_name(name=name)
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"search agent name appear error: {err}")
#
#     @classmethod
#     def check_repeat_name(cls, name: str):
#         try:
#             result = AgentService.check_repeat_name(name=name)
#             if len(result) != 0:
#                 return True
#             else:
#                 return False
#         except Exception as err:
#             logger.error(f"check repeat agent name appear error: {err}")
#
#     @classmethod
#     def check_name_iscustom(cls, name: str):
#         try:
#             data = AgentService.select_agent_by_name(name)
#             return data[0][0].is_custom
#         except Exception as err:
#             logger.error(f"get code by name is appear error: {err}")
#
# class MessageLike:
#
#     @classmethod
#     def create_message_like(cls, user_input: str, agent_output: str):
#         try:
#             MessageLikeService.create_message_like(user_input=user_input, agent_output=agent_output)
#
#         except Exception as err:
#             logger.error(f"create message like is appear error: {err}")
#
#     @classmethod
#     def get_message_like(cls):
#         try:
#             data = MessageLikeService.get_message_like()
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"get message like is appear error: {err}")
#
# class MessageDown:
#
#     @classmethod
#     def create_message_down(cls, user_input: str, agent_output: str):
#         try:
#             MessageDownService.create_message_down(user_input=user_input, agent_output=agent_output)
#
#         except Exception as err:
#             logger.error(f"create message down is appear error: {err}")
#
#     @classmethod
#     def get_message_down(cls):
#         try:
#             data = MessageDownService.get_message_down()
#             result = []
#             for item in data:
#                 result.append(item[0])
#             return result
#         except Exception as err:
#             logger.error(f"get message down is appear error: {err}")
