import json
import lark_oapi as lark
from lark_oapi.api.drive.v1 import *
from pydantic import Field
from typing import Optional


def list_folder_files(
        folder_token: str = Field("", description="文件夹token。不填或为空时获取用户云空间根目录清单（不支持分页）"),
        page_size: int = Field(20, description="每页显示的数据项数量。若获取根目录清单，将返回全部数据", ge=1, le=200),
        order_by: str = Field("EditedTime", description="文件排序字段, 只允许EditedTime, CreatedTime"),
        direction: str = Field("DESC", description="排序方向，允许ASC, DESC"),
        user_id_type: str = Field("open_id", description="用户ID类型，允许open_id, union_id, user_id"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """获取文件夹下的文件列表，成功返回文件列表信息，失败返回报错信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: ListFileRequest = ListFileRequest.builder() \
        .page_size(page_size) \
        .folder_token(folder_token) \
        .order_by(order_by) \
        .direction(direction) \
        .user_id_type(user_id_type) \
        .build()

    # 发起请求
    response: ListFileResponse = client.drive.v1.file.list(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.drive.v1.file.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)
