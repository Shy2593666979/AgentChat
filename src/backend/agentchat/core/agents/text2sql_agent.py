import json
import re
import pymysql
from typing import Dict
from loguru import logger
from urllib.parse import urlparse
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agentchat.prompts.chat import Text2SQLGeneratePrompt, Text2SQLSummaryPrompt
from agentchat.core.models.manager import ModelManager
from agentchat.settings import app_settings

class Text2SQLAgent:
    def __init__(self, db_config: Dict=None):
        self.client = ModelManager.get_conversation_model()

        # 初始化数据库连接
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = self._get_config_from_url()
        self.conn = pymysql.connect(**db_config, cursorclass=pymysql.cursors.DictCursor)

        # 获取 Schema 缓存（避免每次问答都查库）
        self.schema_str = self._get_database_schema()

    def _get_config_from_url(self):
        # 解析 URL
        parsed = urlparse(app_settings.mysql.get("endpoint"))

        # 构建配置字典
        db_config = {
            "host": parsed.hostname,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip('/'),
            "port": parsed.port or 3306,  # 如果 URL 里没写端口，默认 3306
            "charset": "utf8mb4"  # 推荐默认加上，支持中文和表情符号
        }
        return db_config

    def _get_database_schema(self):
        """
        获取数据库的所有表结构，拼接成字符串。
        """
        schema_info = []
        try:
            with self.conn.cursor() as cursor:
                # 获取所有表名
                cursor.execute("SHOW TABLES")
                tables = [list(row.values())[0] for row in cursor.fetchall()]

                for table in tables:
                    # 获取表定义 (Create Table 语句)
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    create_stmt = cursor.fetchone()['Create Table']
                    # 简化一下，只保留核心结构，节省 Token
                    schema_info.append(f"Table: {table}\nSchema: {create_stmt}\n")
        except Exception as e:
            print(f"Error fetching schema: {e}")

        return "\n".join(schema_info)

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
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result, None
        except Exception as e:
            return None, str(e)

    def run(self, user_query, max_retries=3):
        """
        Agent 的主入口：生成 -> 执行 -> (如果出错)修正 -> 总结
        """
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

            logger.info(f"(第 {attempt + 1} 次尝试) 生成 SQL: {current_sql}")

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
        "charset": "utf8mb4"
    }


    agent = Text2SQLAgent(db_config=DB_CONFIG)

    # 测试提问
    answer = agent.run("在这个月消费金额最高的前3个用户的名字和总金额是多少？")
    print("最终回答:\n", answer)