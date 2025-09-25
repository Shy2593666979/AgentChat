import json
import uuid

import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from pydantic import Field
from typing import List


def create_chat_member(user_id_type: str = Field(default="open_id",
                                                           description="用户ID类型，可选值：open_id、union_id、user_id。"),
                       chat_name: str = Field(..., description="群聊名称，不能为空"),
                       chat_description: str = Field(..., description="群聊的简要描述"),
                       owner_id: str = Field(..., description="群主的用户ID（open_id格式）"),
                       user_id_list: List[str] = Field(..., description="创建群聊时拉入的用户ID列表（open_id格式）"),
                       bot_id_list: List[str] = Field(..., description="群聊中添加的机器人ID列表， 如果没有可设置为[]"),
                       chat_avatar: str = Field(default="default-avatar_44ae0ca3-e140-494b-956f-78091e348435",
                                                description="群聊的图标链接"),
                       app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
                       app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")):
    """创建飞书群聊，成功返回群聊信息，失败返回报错信息"""
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateChatRequest = CreateChatRequest.builder() \
        .user_id_type(user_id_type) \
        .set_bot_manager(False) \
        .request_body(CreateChatRequestBody.builder()
                      .avatar(chat_avatar)
                      .name(chat_name)
                      .description(chat_description)
                      .owner_id(owner_id)
                      .user_id_list(user_id_list)
                      .bot_id_list(bot_id_list)
                      .group_message_type("chat")
                      .chat_mode("group")
                      .chat_type("private")
                      .join_message_visibility("all_members")
                      .leave_message_visibility("all_members")
                      .membership_approval("no_approval_required")
                      .restricted_mode_setting(RestrictedModeSetting.builder()
                                               .status(False)
                                               .screenshot_has_permission_setting("all_members")
                                               .download_has_permission_setting("all_members")
                                               .message_has_permission_setting("all_members")
                                               .build())
                      .urgent_setting("all_members")
                      .video_conference_setting("all_members")
                      .edit_permission("all_members")
                      .hide_member_count_setting("all_members")
                      .build()) \
        .build()

    # 发起请求
    response: CreateChatResponse = client.im.v1.chat.create(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.chat.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return f"client.im.v1.chat.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    return lark.JSON.marshal(response.data, indent=4)
