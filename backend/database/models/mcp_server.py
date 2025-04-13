from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4
import pytz

class MCPServerTable(SQLModel, table=True):
    mcp_server_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    mcp_server_path: str = Field(description="MCP Server脚本所在位置")
    mcp_server_command: str = Field(description="MCP Server脚本执行命令, python or npx ...")
    mcp_server_env: str = Field(description="MCP Server脚本环境变量")
    user_id: str = Field(description='MCP Server对应的创建用户')
    name: str = Field(default="MCP Server", description="MCP Server名称")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))