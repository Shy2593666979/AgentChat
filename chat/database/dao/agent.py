from datetime import datetime
from database.models.agent import AgentTable
from sqlmodel import Session
from sqlalchemy import select, and_, update, desc, delete
from utils.helpers import delete_img
from database import engine

class AgentDao:

    @classmethod
    def _get_agent_sql(cls, name: str, description: str, logo: str, parameter: str, type: str, code: str, isCustom: bool):
        agent = AgentTable(name=name,
                           description=description,
                           logo=logo,
                           parameter=parameter,
                           type=type,
                           code=code,
                           isCustom=isCustom)
        return agent

    @classmethod
    def create_agent(cls, name: str, description: str, logo: str, parameter: str, type: str, code: str, isCustom: bool):
        with Session(engine) as session:
            session.add(cls._get_agent_sql(name, description, logo, parameter, type, code, isCustom))
            session.commit()

    @classmethod
    def get_agent(cls):
        with Session(engine) as session:
            sql = select(AgentTable).order_by(desc(AgentTable.createTime))
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_type(cls, type: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.type == type)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_agent_by_custom(cls, isCustom: bool):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.isCustom == isCustom)
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_agent_by_name_type(cls, name: str, type: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(and_(AgentTable.name == name, AgentTable.type == type))
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_agent_by_id(cls, id: str):
        with Session(engine) as session:
            sql = delete(AgentTable).where(AgentTable.id == id)
            session.exec(sql)
            # 删除agent的logo地址
            agent_logo = cls._get_logo_by_id(id)
            delete_img(logo=agent_logo)
            session.commit()

    @classmethod
    def _get_logo_by_id(cls, id: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo

    @classmethod
    def check_repeat_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name == name)
            result = session.exec(sql).all()
            return result

    @classmethod
    def search_agent_name(cls, name: str):
        with Session(engine) as session:
            sql = select(AgentTable).where(AgentTable.name.like(f'%{name}%'))
            result = session.exec(sql).all()
            return result

    @classmethod
    def update_agent_by_id(cls, id: str, name: str, description: str, logo: str, parameter: str, type: str, code: str):
        with Session(engine) as session:
            # 构建 update 语句
            update_values = {
                'createTime': datetime.utcnow()
            }
            if name is not None:
                update_values['name'] = name
            if description is not None:
                update_values['description'] = description
            if parameter is not None:
                update_values['parameter'] = parameter
            if type is not None:
                update_values['type'] = type
            if code is not None:
                update_values['code'] = code
            if logo is not None:
                # 删除agent的logo地址
                agent_logo = cls._get_logo_by_id(id)
                delete_img(logo=agent_logo)
                update_values['logo'] = logo

            sql = update(AgentTable).where(AgentTable.id == id).values(**update_values)
            session.exec(sql)
            session.commit()
            # sql = select(AgentTable).where(AgentTable.id == id)
            # agent = session.exec(sql).one()
            #
            # if name is not None:
            #     agent.name = name
            # if description is not None:
            #     agent.description = description
            # if parameter is not None:
            #     agent.parameter = parameter
            # if type is not None:
            #     agent.type = type
            # if code is not None:
            #     agent.code = code
            # if logo is not None:
            #     # 删除agent的logo地址
            #     delete_img(logo=logo)
            #     agent.logo = logo
            # agent.createTime = datetime.utcnow()
            #
            # session.add(agent)
            # session.commit()
            # session.refresh()
