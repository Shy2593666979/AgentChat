"""
将 Tool 的 parameters JSON 转换为 MCP JsonSchema 格式
"""

import json
from typing import Any


def parse_input_schema(parameters: str | None) -> dict:
    """将 Tool.parameters JSON 字符串解析为 MCP inputSchema dict"""
    if not parameters:
        return {"type": "object", "properties": {}}

    try:
        schema = json.loads(parameters)
    except (json.JSONDecodeError, TypeError):
        return {"type": "object", "properties": {}}

    properties = schema.get("properties")
    if properties is not None:
        # 已经是 MCP JSON Schema 格式
        return {
            "type": schema.get("type", "object"),
            "properties": properties,
            "required": schema.get("required"),
            "additionalProperties": schema.get("additionalProperties"),
        }

    # OpenAPI 参数格式转换
    return _parse_openapi_schema(schema)


def _parse_openapi_schema(schema: dict) -> dict:
    properties: dict[str, Any] = {}
    required: list[str] = []

    # 处理 OpenAPI parameters (path, query, header, cookie)
    for param in schema.get("parameters", []):
        in_ = param.get("in", "query")
        name = param.get("name", "")
        is_required = param.get("required", False)
        description = param.get("description", name)
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        default_val = param_schema.get("default")

        if is_required:
            required.append(name)

        prop_def: dict[str, Any] = {
            "type": param_type,
            "description": description,
            "x-position": in_,  # 保存参数位置信息
        }
        if default_val is not None:
            prop_def["default"] = default_val
        if param_type == "array" and param_schema.get("items") is not None:
            prop_def["items"] = param_schema.get("items")

        properties[name] = prop_def

    # 处理 requestBody
    request_body = schema.get("requestBody")
    if request_body:
        content = request_body.get("content", {})

        for content_type_full, content_def in content.items():
            content_type = content_type_full.split(";")[0].strip()
            rb_schema = content_def.get("schema", {})
            rb_type = rb_schema.get("type", "object")

            if content_type in ("application/json", "application/x-www-form-urlencoded"):
                # requestBody 是 object - 扁平化到顶层
                if rb_type == "object":
                    rb_required = rb_schema.get("required", [])
                    for pname, pdef in rb_schema.get("properties", {}).items():
                        entry: dict[str, Any] = {
                            "type": pdef.get("type", "string"),
                            "description": pdef.get("description", ""),
                            "x-position": "body",  # 标记为 body 参数
                        }
                        if pdef.get("type") == "array" and pdef.get("items") is not None:
                            entry["items"] = pdef.get("items")
                        if "default" in pdef:
                            entry["default"] = pdef.get("default")

                        properties[pname] = entry

                    for name in rb_required:
                        if name not in required:
                            required.append(name)

                # requestBody 不是 object，保留 requestBody 字段
                elif rb_type == "array":
                    properties["requestBody"] = {
                        "type": "array",
                        "items": rb_schema.get("items"),
                        "x-position": "body",
                    }
                    if request_body.get("required", False) and "requestBody" not in required:
                        required.append("requestBody")

                else:
                    properties["requestBody"] = {
                        "type": rb_type,
                        "x-position": "body",
                    }
                    if request_body.get("required", False) and "requestBody" not in required:
                        required.append("requestBody")

                break

            elif content_type == "application/octet-stream":
                properties["requestBody"] = {
                    "type": "string",
                    "description": "Binary file content",
                    "x-position": "body",
                }
                if request_body.get("required", False) and "requestBody" not in required:
                    required.append("requestBody")
                break

    return {
        "type": "object",
        "properties": properties,
        "required": required if required else [],
        "additionalProperties": False,
    }


def tool_to_mcp_schema(tool) -> dict:
    """将 Tool ORM 对象转换为 MCP tool schema dict（去除 x-position 元数据）"""
    input_schema = parse_input_schema(tool.parameters)
    
    # 清理 x-position 元数据
    cleaned_properties = {}
    for prop_name, prop_def in input_schema.get("properties", {}).items():
        cleaned_def = {k: v for k, v in prop_def.items() if not k.startswith("x-")}
        cleaned_properties[prop_name] = cleaned_def
    
    input_schema["properties"] = cleaned_properties
    
    return {
        "name": tool.name,
        "description": tool.description or "",
        "inputSchema": input_schema,
    }


def build_error_result(message: str) -> dict:
    return {
        "content": [{"type": "text", "text": f"Error: {message}"}],
        "isError": True,
    }
