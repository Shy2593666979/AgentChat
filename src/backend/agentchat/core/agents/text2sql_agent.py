import json
import re
from typing import Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.engine import URL
from sqlalchemy.schema import CreateTable

from agentchat.database.connection import (
    create_sync_database_engine,
    resolve_database_urls,
)
from agentchat.prompts.completion import Text2SQLGeneratePrompt, Text2SQLSummaryPrompt
from agentchat.settings import app_settings


class Text2SQLAgent:
    def __init__(self, db_config: Dict | str | None = None):
        # Initialize the LLM only when run() is invoked, not for schema inspection.
        self.client = None
        self.db_config = db_config
        url = self._get_database_url(db_config)
        self.engine = create_sync_database_engine(url)
        self.conn = self.engine.connect()
        self.schema_str = self._get_database_schema()

    def _get_database_url(self, db_config):
        if db_config is None:
            from agentchat.database import engine
            return engine.url
        if isinstance(db_config, str):
            return resolve_database_urls(
                {
                    "url": db_config,
                }
            ).sync
        if db_config.get("url") or db_config.get("endpoint"):
            return resolve_database_urls(db_config).sync
        # Preserve the existing MySQL dictionary constructor, including escaped passwords.
        return URL.create("mysql+pymysql", username=db_config.get("user"),
                          password=db_config.get("password"), host=db_config.get("host", "localhost"),
                          port=db_config.get("port", 3306), database=db_config.get("database"))

    def _get_database_schema(self):
        schemas = ["Database dialect: " + self.engine.dialect.name]
        for name in inspect(self.conn).get_table_names():
            table = Table(name, MetaData(), autoload_with=self.conn)
            schemas.append("Table: " + name + "\nSchema: " + str(CreateTable(table).compile(self.conn)))
        self.conn.rollback()
        return "\n".join(schemas)

    def close(self):
        self.conn.close()
        self.engine.dispose()

    def _clean_sql(self, sql_text):
        """
        清洗 LLM 输出，去除 Markdown 符号
        """
        # 去除 ```sql 和 ``` 
        sql_text = re.sub(r"```sql", "", sql_text, flags=re.IGNORECASE)
        sql_text = re.sub(r"```", "", sql_text)
        return sql_text.strip()

    def _execute_sql(self, sql):
        """
        执行 SQL，返回结果或错误信息
        """
        # 安全检查：简单防止非查询语句 (生产环境建议使用只读账号)
        if not sql.upper().startswith("SELECT"):
            return None, "Error: Only SELECT queries are allowed."

        try:
            result = [dict(row) for row in self.conn.exec_driver_sql(sql).mappings().all()]
            self.conn.rollback()
            return result, None
        except Exception as e:
            self.conn.rollback()
            return None, str(e)

    def run(self, user_query, max_retries=3):
        """
        Agent 的主入口：生成 -> 执行 -> (如果出错)修正 -> 总结
        """
        if self.client is None:
            from agentchat.core.models.manager import ModelManager
            self.client = ModelManager.get_chat_model()
        system_prompt = Text2SQLGeneratePrompt.format(schema=self.schema_str)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        current_sql = ""
        # 循环生成与执行 (Self-Correction Loop)
        for attempt in range(max_retries):
            # 调用 LLM 生成 SQL
            response = self.client.invoke(messages)

            raw_content = response.content
            current_sql = self._clean_sql(raw_content)

            logger.debug(f"(第 {attempt + 1} 次尝试) 生成 SQL: {current_sql}")

            # 执行 SQL
            data, error = self._execute_sql(current_sql)

            if error:
                logger.error(f"Text2SQL-Agent 执行出错: {error}")
                # 将错误信息回传给 LLM 进行修正
                messages.append(AIMessage(content=current_sql))
                messages.append(HumanMessage(content=f"SQL 执行报错: {error}。请根据 Schema 修正 SQL。"))
            else:
                logger.info(f"Text2SQL-Agent 执行成功，获取到 {len(data)} 条数据")
                return self._synthesize_answer(user_query, current_sql, data)

        return "抱歉，尝试多次后仍无法生成正确的 SQL。"

    def _synthesize_answer(self, query, sql, data):
        """
        将数据转化为自然语言回答
        """
        summary_prompt = Text2SQLSummaryPrompt.format(query=query, sql=sql, result=json.dumps(data, default=str, ensure_ascii=False))

        response = self.client.invoke(HumanMessage(content=summary_prompt))
        return response.content



if __name__ == "__main__":
    # 配置你的 MySQL
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "password",
        "database": "agentchat",  # 换成你的库名
        "charset": "utf8mb4",
    }


    agent = Text2SQLAgent(db_config=DB_CONFIG)

    # 测试提问
    answer = agent.run("在这个月消费金额最高的前3个用户的名字和总金额是多少？")
    print("最终回答:\n", answer)
