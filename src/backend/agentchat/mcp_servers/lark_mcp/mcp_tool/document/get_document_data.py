import json
import lark_oapi as lark
from lark_oapi.api.docx.v1 import *
from pydantic import Field
from typing import Optional


def get_document(
        document_id: str = Field(..., description="文档ID"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """获取文档内容，成功返回文档内容，失败返回报错信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: RawContentDocumentRequest = RawContentDocumentRequest.builder() \
        .document_id(document_id) \
        .lang(0) \
        .build()

    # 发起请求
    response: RawContentDocumentResponse = client.docx.v1.document.raw_content(request)

    # 处理失败返回
    if not response.success():
        error_message = f"client.docx.v1.document.raw_content failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        return error_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)