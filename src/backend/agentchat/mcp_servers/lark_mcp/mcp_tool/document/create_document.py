import json
import lark_oapi as lark
from lark_oapi.api.docx.v1 import *
from pydantic import Field
from typing import Optional


def create_document(
        folder_token: str = Field(None, description="文件夹token, 没有传入的话在根目录中创建"),
        title: str = Field(..., description="文档标题"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """创建文档，成功返回文档信息，失败返回报错信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateDocumentRequest = CreateDocumentRequest.builder() \
        .request_body(CreateDocumentRequestBody.builder()
                      .folder_token(folder_token)
                      .title(title)
                      .build()) \
        .build()

    # 发起请求
    response: CreateDocumentResponse = client.docx.v1.document.create(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.docx.v1.document.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)