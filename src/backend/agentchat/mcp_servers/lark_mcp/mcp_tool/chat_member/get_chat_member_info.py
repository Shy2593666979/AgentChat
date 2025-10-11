import json

import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from pydantic import Field
from typing import List


def get_chat_member_info(user_id_type: str = Field(default="open_id",
                                                             description="用户ID类型，可选值：open_id、union_id、user_id。"),
                         chat_id: str = Field(..., description="群聊的ID"),
                         app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
                         app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")):
    """获取群聊的群信息，成功返回群聊信息，失败返回报错信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: GetChatRequest = GetChatRequest.builder() \
        .chat_id(chat_id) \
        .user_id_type(user_id_type) \
        .build()

    # 发起请求
    response: GetChatResponse = client.im.v1.chat.get(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.im.v1.chat.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)
