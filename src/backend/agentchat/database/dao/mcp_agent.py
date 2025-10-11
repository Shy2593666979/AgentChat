from datetime import datetime

from typing import List
from agentchat.database.models.mcp_agent import MCPAgentTable
from sqlmodel import Session, select, and_, update, desc, delete
from agentchat.utils.helpers import delete_img
from agentchat.database.session import session_getter


class MCPAgentDao:

    @classmethod
    def _get_mcp_agent_sql(cls, name: str, description: str, logo: str, user_id: str, knowledges_id: List[str],
                           llm_id: str, mcp_servers_id: List[str], is_custom: bool, enable_memory: bool):
        agent = MCPAgentTable(name=name,
                              logo=logo,
                              user_id=user_id,
                              llm_id=llm_id,
                              mcp_servers_id=mcp_servers_id,
                              description=description,
                              knowledges_id=knowledges_id,
                              is_custom=is_custom,
                              enable_memory=enable_memory)
        return agent

    @classmethod
    def create_mcp_agent(cls, name: str, description: str, logo: str, user_id: str, knowledges_id: List[str],
                         llm_id: str, mcp_servers_id: List[str], is_custom: bool, enable_memory: bool):
        with session_getter() as session:
            session.add(cls._get_mcp_agent_sql(name, description, logo, user_id, knowledges_id, llm_id, mcp_servers_id,
                                               is_custom, enable_memory))
            session.commit()

    @classmethod
    def get_mcp_agent(cls):
        with session_getter() as session:
            sql = select(MCPAgentTable).order_by(desc(MCPAgentTable.create_time))
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_mcp_agent_by_name(cls, name: str):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.name == name)
            result = session.exec(sql).first()
            return result

    @classmethod
    def get_mcp_agent_user_id(cls, agent_id: str):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.id == agent_id)
            agent = session.exec(sql).first()
            return agent

    @classmethod
    def select_mcp_agent_by_custom(cls, is_custom: bool):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.is_custom == is_custom)
            result = session.exec(sql).all()
            return result

    @classmethod
    def delete_mcp_agent_by_id(cls, id: str):
        with session_getter() as session:
            sql = delete(MCPAgentTable).where(MCPAgentTable.id == id)
            session.exec(sql)
            # 删除agent的logo地址
            agent_logo = cls._get_logo_by_id(id)
            delete_img(logo=agent_logo)
            session.commit()

    @classmethod
    def _get_logo_by_id(cls, id: str):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.id == id)
            result = session.exec(sql).all()
            return result[0][0].logo

    @classmethod
    def check_repeat_name(cls, name: str, user_id: str):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(and_(MCPAgentTable.name == name, MCPAgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    def search_mcp_agent_name(cls, name: str, user_id: str):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(and_(MCPAgentTable.name.like(f'%{name}%'),
                                                   MCPAgentTable.user_id == user_id))
            result = session.exec(sql).all()
            return result

    @classmethod
    def get_mcp_agent_by_user_id(cls, user_id: int):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.user_id == user_id)
            result = session.exec(sql).all()
            return result

    @classmethod
    def select_mcp_agent_by_id(cls, agent_id):
        with session_getter() as session:
            sql = select(MCPAgentTable).where(MCPAgentTable.id == agent_id)
            result = session.exec(sql).first()
            return result

    @classmethod
    def update_mcp_agent_by_id(cls, id: str, name: str, description: str, knowledges_id: List[str],
                               logo: str, llm_id: str, mcp_servers_id: List[str], enable_memory: bool):
        with session_getter() as session:
            # 构建 update 语句
            update_values = {}
            if name is not None:
                update_values['name'] = name
            if description is not None:
                update_values['description'] = description
            if llm_id is not None:
                update_values['llm_id'] = llm_id
            if mcp_servers_id is not None:
                update_values['mcp_servers_id'] = mcp_servers_id
            if knowledges_id is not None:
                update_values['knowledges_id'] = knowledges_id
            if enable_memory:
                update_values['enable_memory'] = enable_memory

            if logo is not None:
                # 删除agent的logo地址
                agent_logo = cls._get_logo_by_id(id)
                delete_img(logo=agent_logo)
                update_values['logo'] = logo

            sql = update(MCPAgentTable).where(MCPAgentTable.id == id).values(**update_values)
            session.exec(sql)
            session.commit()
