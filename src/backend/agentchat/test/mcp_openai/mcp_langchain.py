from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, Type, List
from langchain_core.tools import BaseTool, StructuredTool


import logging
import httpx
from agentchat.settings import app_settings


async def request_mcp_call_tools(mcp_tools_args):
    json_data = {
        "mcp_tools_args": mcp_tools_args # case: [{"server_name": "xxx", "url": "xxxx", "type": "xxx", "tool_name": "xxxx", "tool_args": "xxxx"}]
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(app_settings.mcp_base_url + "/call_tools", json=json_data, timeout=30.0)
            response.raise_for_status()
            return response.json()  # 返回字典类型
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Error: HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Error: 请求失败: {str(e)}")


async def call_mcp_tools(mcp_tools_args):
    try:
        response = await request_mcp_call_tools(mcp_tools_args)
        tools_data = response["data"]
        tools_result = "\n".join(tools_data)

        return tools_result
    except Exception as err:
        return err


async def request_mcp_list_tools(mcp_servers):
    servers = []

    for server in mcp_servers:
        servers.append({"server_name": server["name"], "url": server["url"], "type": server["type"]})
    json_data = {
        "mcp_servers": servers  # case: [{"server_name": "xxxx", "url": "xxxx", "type": "xxxx"}]
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(app_settings.mcp_base_url + "/mcp_tools", json=json_data, timeout=30.0)
            response.raise_for_status()
            return response.json()  # 返回字典类型
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Error: HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Error: 请求失败: {str(e)}")


async def list_mcp_tools(mcp_servers):
    response = await request_mcp_list_tools(mcp_servers)
    data = response["data"]
    tools_result = []
    for key, value in data.items():
        for tool in value:
            tools_result.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            })
    return tools_result


def convert_base_tool(tool_name, tool_description, schema: Dict[str, Any]):
    schema_model = create_model_from_schema(tool_name, schema)
    return StructuredTool(
        name=tool_name,
        description=tool_description,
        args_schema=schema_model
    )


# 从mcp服务返回来的数据是 json schema格式的数据，但是BaseTool的输入参数需要是基于BaseModel类
# TODO: 将Chat Agent那块的MCP Tool单独调用
def create_model_from_schema(tool_name: str, schema: Dict[str, Any]) -> type[BaseModel]:
    """
    从JSON模式动态创建Pydantic BaseModel类
    :param schema: JSON模式数据（如 {'type': 'object', 'properties': ..., 'required': ...}）
    :return: 动态生成的Pydantic模型类
    """
    if schema.get('type') != 'object':
        raise ValueError("仅支持对象类型（type: object）的JSON模式")

    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # 解析每个字段的配置
    fields = {}
    for field_name, field_schema in properties.items():
        field_type = field_schema.get('type', 'string')
        description = field_schema.get('description', '')

        # 处理字段类型
        if field_type == 'string':
            py_type = str
        elif field_type == 'number':
            py_type = float
        elif field_type == 'integer':
            py_type = int
        elif field_type == 'boolean':
            py_type = bool
        elif field_type == 'array':
            items_schema = field_schema.get('items')
            if items_schema is None:
                raise ValueError(f"数组字段 {field_name} 缺少 'items' 定义")
            item_type = handle_single_type(items_schema)
            py_type = List[item_type]
        else:
            py_type = 'string'
            logging.info("暂不支持类型: {field_type}  default: string")
            # raise NotImplementedError(f"暂不支持类型: {field_type}")

        # 设置默认值：必填字段（在required中）无默认值（用...），选填字段默认值为None
        default = ... if field_name in required else None

        # 去除Type、Desc字段的信息塞进description中
        for key in list(field_schema.keys()):  # 使用 list() 创建键的副本
            if key in ('type', 'description'):
                del field_schema[key]  # 安全地删除键
        description = description + str(field_schema)
        # 构建字段定义（使用Field指定描述）
        fields[field_name] = (py_type, Field(default, description=description))

    tool_name = convert_to_model_name(tool_name)
    # 动态创建模型类
    if tool_name:
        model_name = tool_name
    else:
        model_name = 'DynamicModel'  # 可从模式中获取类名，默认用DynamicModel
    return create_model(model_name, **fields)


def handle_single_type(field_schema: Dict[str, Any]):
    field_type = field_schema.get('type')
    if field_type == 'string':
        return str
    elif field_type == 'number':
        return float
    elif field_type == 'integer':
        return int
    elif field_type == 'boolean':
        return bool
    else:
        logging.error(f"暂不支持类型: {field_type}")
        return str
        # raise NotImplementedError(f"暂不支持类型: {field_type}")


def convert_to_model_name(input_string):
    # case: google_search  ---->  GoogleSearchModel
    words = input_string.split('_')
    # 首字母大写并拼接
    model_name = ''.join(word.capitalize() for word in words)
    # 添加后缀 "Model"
    return f"{model_name}Model"


async def is_mcp_tool(tool_name):
    """
    根据工具名判断是否属于MCP服务
    """
    if tool_name.endswith("_mcp"):
        return True
    return False
    # mcp_server = await MCPServerService.get_server_from_tool(tool_name)

    # if len(mcp_server) == 0:
    #     return False
    # else:
    #     return True