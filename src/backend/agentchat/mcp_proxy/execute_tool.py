import base64
import json
import httpx
from typing import Any
from urllib.parse import urlencode

from agentchat.database.models.register_mcp_tool import RegisterMcpTool
from loguru import logger

class RegisterMcpToolExecute:

    @classmethod
    async def execute_http_tool(cls, tool: RegisterMcpTool, arguments: dict) -> dict:
        """根据 Tool 的 api_info 执行 HTTP 请求，返回 MCP CallToolResult 格式"""
        api_info = tool.api_info or {}
        base_url = api_info.get("base_url", "")
        path = api_info.get("path", "")
        method = api_info.get("method", "GET").upper()
        content_type = api_info.get("content_type", "application/json")

        full_url = base_url + path
        path_vars: dict[str, str] = {}
        query_params: dict[str, str] = {}
        headers: dict[str, str] = {}
        cookies: dict[str, str] = {}
        body_data: dict[str, Any] = {}

        # 解析 parameters schemas 获取位置信息
        import json
        try:
            param_schema = json.loads(tool.parameters) if tool.parameters else {}
        except (json.JSONDecodeError, TypeError):
            param_schema = {}
        
        properties = param_schema.get("properties", {})

        # 根据 x-position 分配参数到正确位置
        for arg_name, arg_value in arguments.items():
            prop_def = properties.get(arg_name, {})
            position = prop_def.get("x_position", "query")  # 默认 query
            
            if position == "path":
                path_vars[arg_name] = str(arg_value)
            elif position == "query":
                query_params[arg_name] = str(arg_value)
            elif position == "header":
                headers[arg_name] = str(arg_value)
            elif position == "cookie":
                cookies[arg_name] = str(arg_value)
            elif position == "body":
                # 特殊处理 requestBody（非 object 类型）
                if arg_name == "requestBody":
                    body_data = arg_value  # 直接使用整个值
                else:
                    body_data[arg_name] = arg_value

        # 替换路径变量
        for var_name, var_val in path_vars.items():
            full_url = full_url.replace(f"{{{var_name}}}", var_val)

        # 编码 body
        body_bytes: bytes | None = None
        if body_data:
            body_bytes = cls._encode_body(body_data, content_type)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    method=method,
                    url=full_url,
                    params=query_params or None,
                    headers={**headers, "Content-Type": content_type} if body_bytes else headers,
                    cookies=cookies or None,
                    content=body_bytes,
                )
            result: dict[str, Any] = {
                "isError": not resp.is_success,
                "content": [{"type": "text", "text": resp.text}],
            }

            if resp.is_success and "application/json" in resp.headers.get("content-type", ""):
                try:
                    result["structuredContent"] = resp.json()
                except Exception:
                    pass
            return result
        except Exception as e:
            logger.error(f"HTTP request failed for tool {tool.name}: {e}")
            return {"isError": True, "content": [{"type": "text", "text": str(e)}]}

    @classmethod
    def _encode_body(cls, body: Any, content_type: str) -> bytes | None:
        ct = content_type.split(";")[0].strip()
        if ct == "application/json":
            return json.dumps(body).encode()
        elif ct == "application/x-www-form-urlencoded":
            if isinstance(body, dict):
                return urlencode(body).encode()
        elif ct == "application/octet-stream":
            if isinstance(body, str):
                return base64.b64decode(body)
        return None