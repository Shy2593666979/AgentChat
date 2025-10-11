import json
import lark_oapi as lark
from lark_oapi.api.drive.v1 import *
from pydantic import Field
from typing import Optional


def create_folder(
        name: str = Field(..., description="文件夹名称"),
        folder_token: str = Field("", description="父文件夹token"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """创建文件夹，成功返回文件夹信息，失败返回报错信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateFolderFileRequest = CreateFolderFileRequest.builder() \
        .request_body(CreateFolderFileRequestBody.builder()
                      .name(name)
                      .folder_token(folder_token)
                      .build()) \
        .build()

    # 发起请求
    response: CreateFolderFileResponse = client.drive.v1.file.create_folder(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.drive.v1.file.create_folder failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)