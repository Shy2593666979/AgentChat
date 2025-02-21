# -------------------------------
# 该文件目前版本已弃用
# -------------------------------

# from datetime import  datetime
# from database.models import HistoryTable, DialogTable
# from database.models import MessageDownTable, MessageLikeTable, AgentTable
# from sqlmodel import SQLModel, create_engine, Session
# from sqlalchemy import select, and_, update, desc, delete
# from config.service_config import  MYSQL_URL
# from utils.helpers import delete_img
#
# engine = create_engine(MYSQL_URL, connect_args={"charset": "utf8mb4"})
#
# class HistoryService:
#
#     @classmethod
#     def _get_history_sql(cls, role: str, content: str, dialog_id: str):
#         history = HistoryTable(content=content, role=role, dialog_id=dialog_id)
#         return history
#
#     @classmethod
#     def create_history(cls, role: str, content: str, dialog_id: str):
#         with Session(engine) as session:
#             session.add(cls._get_history_sql(role, content, dialog_id))
#             session.commit()
#
#     @classmethod
#     def select_history(cls, dialog_id: str, k: int):
#         with Session(engine) as session:
#             sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
#             result = session.exec(sql).all()
#
#             # 每次最多取当前会话的k条历史记录
#             if len(result) > k:
#                 result = result[-k:]
#             return result
#
#     @classmethod
#     def get_dialog_history(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = select(HistoryTable).where(HistoryTable.dialog_id == dialog_id).order_by(HistoryTable.create_time)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def delete_history_by_dialog_id(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = delete(HistoryTable).where(HistoryTable.dialog_id == dialog_id)
#             session.exec(sql)
#             session.commit()
#
# class DialogService:
#
#     @classmethod
#     def _get_dialog_sql(cls, name: str, agent: str):
#         dialog = DialogTable(name=name, agent=agent)
#         return dialog
#
#     @classmethod
#     def create_dialog(cls, name, agent: str):
#         with Session(engine) as session:
#             dialog = cls._get_dialog_sql(name, agent)
#             session.add(dialog)
#             session.commit()
#             return dialog.dialog_id
#
#     @classmethod
#     def select_dialog(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
#             result = session.exec(sql).all()
#
#             return result
#
#     @classmethod
#     def get_list_dialog(cls):
#         with Session(engine) as session:
#             sql = select(DialogTable).order_by(desc(DialogTable.create_time))
#             result = session.exec(sql).all()
#
#             return result
#
#     @classmethod
#     def get_agent_by_dialog_id(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def update_dialog_time(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = update(DialogTable).where(DialogTable.dialog_id == dialog_id).values(create_time=datetime.utcnow())
#             session.exec(sql)
#             session.commit()
#             # dialog = session.exec(sql).one()
#             #
#             # dialog.create_time = datetime.utcnow()
#             #
#             # session.add(dialog)
#             # session.commit()
#             # session.refresh()
#
#     @classmethod
#     def delete_dialog_by_id(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = delete(DialogTable).where(DialogTable.dialog_id == dialog_id)
#             session.exec(sql)
#             session.commit()
#
#     @classmethod
#     def check_dialog_iscustom(cls, dialog_id: str):
#         with Session(engine) as session:
#             sql = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
#             result = session.exec(sql).all()
#
#             return result
#
# class AgentService:
#
#     @classmethod
#     def _get_agent_sql(cls, name: str, description: str, logo: str, parameter: str, schema: str, code: str, is_custom: bool):
#         agent = AgentTable(name=name,
#                            description=description,
#                            logo=logo,
#                            parameter=parameter,
#                            schema=schema,
#                            code=code,
#                            is_custom=is_custom)
#         return agent
#
#     @classmethod
#     def create_agent(cls, name: str, description: str, logo: str, parameter: str, schema: str, code: str, is_custom: bool):
#         with Session(engine) as session:
#             session.add(cls._get_agent_sql(name, description, logo, parameter, schema, code, is_custom))
#             session.commit()
#
#     @classmethod
#     def get_agent(cls):
#         with Session(engine) as session:
#             sql = select(AgentTable).order_by(desc(AgentTable.create_time))
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def select_agent_by_name(cls, name: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.name == name)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def select_agent_by_type(cls, schema: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.schema == schema)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def select_agent_by_custom(cls, is_custom: bool):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.is_custom == is_custom)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def get_agent_by_name_type(cls, name: str, schema: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.schema == schema))
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def delete_agent_by_id(cls, id: str):
#         with Session(engine) as session:
#             sql = delete(AgentTable).where(AgentTable.id == id)
#             session.exec(sql)
#             # 删除agent的logo地址
#             agent_logo = cls._get_logo_by_id(id)
#             delete_img(logo=agent_logo)
#             session.commit()
#
#     @classmethod
#     def _get_logo_by_id(cls, id: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.id == id)
#             result = session.exec(sql).all()
#             return result[0][0].logo
#
#     @classmethod
#     def check_repeat_name(cls, name: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.name == name)
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def search_agent_name(cls, name: str):
#         with Session(engine) as session:
#             sql = select(AgentTable).where(AgentTable.name.like(f'%{name}%'))
#             result = session.exec(sql).all()
#             return result
#
#     @classmethod
#     def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, schema: str, code: str):
#         with Session(engine) as session:
#             # 构建 update 语句
#             update_values = {
#                 'create_time': datetime.utcnow()
#             }
#             if name is not None:
#                 update_values['name'] = name
#             if description is not None:
#                 update_values['description'] = description
#             if parameter is not None:
#                 update_values['parameter'] = parameter
#             if schema is not None:
#                 update_values['schema'] = schema
#             if code is not None:
#                 update_values['code'] = code
#             if logo is not None:
#                 # 删除agent的logo地址
#                 agent_logo = cls._get_logo_by_id(id)
#                 delete_img(logo=agent_logo)
#                 update_values['logo'] = logo
#
#             sql = update(AgentTable).where(AgentTable.id == id).values(**update_values)
#             session.exec(sql)
#             session.commit()
#             # sql = select(AgentTable).where(AgentTable.id == id)
#             # agent = session.exec(sql).one()
#             #
#             # if name is not None:
#             #     agent.name = name
#             # if description is not None:
#             #     agent.description = description
#             # if parameter is not None:
#             #     agent.parameter = parameter
#             # if schema is not None:
#             #     agent.schema = schema
#             # if code is not None:
#             #     agent.code = code
#             # if logo is not None:
#             #     # 删除agent的logo地址
#             #     delete_img(logo=logo)
#             #     agent.logo = logo
#             # agent.create_time = datetime.utcnow()
#             #
#             # session.add(agent)
#             # session.commit()
#             # session.refresh()
#
# class MessageLikeService:
#
#     @classmethod
#     def _get_message_like_sql(cls, user_input: str, agent_output: str):
#         like = MessageLikeTable(user_input=user_input, agent_output=agent_output)
#         return like
#
#     @classmethod
#     def create_message_like(cls, user_input: str, agent_output: str):
#         with Session(engine) as session:
#             session.add(cls._get_message_like_sql(user_input, agent_output))
#             session.commit()
#
#     @classmethod
#     def get_message_like(cls):
#         with Session(engine) as session:
#             sql = select(MessageLikeTable)
#             result = session.exec(sql).all()
#             return result
#
#
# class MessageDownService:
#
#     @classmethod
#     def _get_message_down_sql(cls, user_input: str, agent_output: str):
#         down = MessageDownTable(user_input=user_input, agent_output=agent_output)
#         return down
#
#     @classmethod
#     def create_message_down(cls, user_input: str, agent_output: str):
#         with Session(engine) as session:
#             session.add(cls._get_message_down_sql(user_input, agent_output))
#             session.commit()
#
#     @classmethod
#     def get_message_down(cls):
#         with Session(engine) as session:
#             sql = select(MessageDownTable)
#             result = session.exec(sql).all()
#             return result
