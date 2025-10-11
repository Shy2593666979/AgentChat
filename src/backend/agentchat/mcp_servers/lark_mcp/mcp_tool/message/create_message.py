import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from pydantic import Field
from typing import Optional, Literal
from uuid import uuid4


def create_message(
        receive_id: str = Field(...,
                                description="消息接收者的ID，ID类型与receive_id_type一致。注意：给用户发消息需确保用户在机器人可用范围内；给群组发消息需确保机器人在群内且有发言权限"),
        msg_type: str = Field("text", description="消息类型，支持：text(文本)、post(富文本)"),
        content: dict = Field(...,
                              description='消息内容JSON字符串，需根据msg_type设置对应格式，例如：{"text": "你好，我是飞书机器人"}'),
        receive_id_type: str = Field("open_id", description="接收者ID类型，仅支持open_id类型"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """发送消息，给用户发消息需确保用户在机器人可用范围内；给群组发消息需确保机器人在群内且有发言权限"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    # 将JSON对象转换为JSON转义的字符串
    json_escaped_str = json.dumps(content, ensure_ascii=True)

    # 构造请求对象
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(receive_id)
                      .msg_type(msg_type)
                      .content(json_escaped_str)
                      .uuid(uuid4().hex)
                      .build()) \
        .build()

    # 发起请求
    response: CreateMessageResponse = client.im.v1.message.create(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)
