import argparse
import json

import lark_oapi as lark
from lark_oapi.api.contact.v3 import *
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
mcp = FastMCP("Lark MCP Server")


@mcp.tool(description="能够根据用户的邮箱或者手机号查找用户的信息")
def get_id_user_request(user_id_type: str = Field("open_id", description=""),
                        emails: List[str] = Field(None, description=""),
                        mobiles: List[str] = Field(None, description=""),
                        app_id: str = Field(None, description="xxx"),
                        app_secret: str = Field(None, description="xxxx")):
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_axxxxxxxxxx") \
        .app_secret("Nc1nR0xxxxxxxxxxxxxx") \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: BatchGetIdUserRequest = BatchGetIdUserRequest.builder() \
        .user_id_type(user_id_type) \
        .request_body(BatchGetIdUserRequestBody.builder()
                      .emails(emails)
                      .mobiles(mobiles)
                      .include_resigned(True)
                      .build()) \
        .build()

    # 发起请求
    response: BatchGetIdUserResponse = client.contact.v3.user.batch_get_id(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.contact.v3.user.batch_get_id failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return f"client.contact.v3.user.batch_get_id failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return str(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lark MCP Server")
    parser.add_argument("--transport", type=str, default="sse", choices=["sse", "stdio", "streamable-http"],
                        help="Transport type")
    args = parser.parse_args()
    mcp.run(transport=args.transport)
