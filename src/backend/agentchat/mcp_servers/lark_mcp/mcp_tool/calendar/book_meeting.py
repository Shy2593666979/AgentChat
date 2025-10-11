import json
import lark_oapi as lark
from lark_oapi.api.vc.v1 import *
from pydantic import Field
from typing import Optional, List, Literal


def book_meeting(
        end_time: int = Field(..., description="会议结束时间，Unix时间戳（秒）"),
        owner_id: str = Field(..., description="会议组织者ID（通常为用户open_id）"),
        topic: str = Field(..., description="会议主题"),
        meeting_initial_type: Literal[1, 2] = Field(1, description="会议初始类型：1：多人会议)"),
        meeting_connect: bool = Field(True, description="该会议是否支持互通，不支持更新"),
        auto_record: bool = Field(True, description="是否自动录制会议"),
        assign_host_list: List[str] = Field(..., description="会议主持人列表，每个元素需包含用户的id"),
        password: str = Field(None, description="会议密码（可选）"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """预约会议（创建会议预约）"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造主持人列表请求体
    host_list = [
        ReserveAssignHost.builder()
        .user_type(1)
        .id(host_info)
        .build()
        for host_info in assign_host_list
    ]

    # 构造请求对象
    request: ApplyReserveRequest = ApplyReserveRequest.builder() \
        .request_body(ApplyReserveRequestBody.builder()
                      .end_time(end_time)
                      .owner_id(owner_id)
                      .meeting_settings(ReserveMeetingSetting.builder()
                                        .topic(topic)
                                        .meeting_initial_type(meeting_initial_type)
                                        .meeting_connect(meeting_connect)
                                        .auto_record(auto_record)
                                        .assign_host_list(host_list)
                                        .password(password)
                                        .build())
                      .build()) \
        .build()

    # 发起请求
    response: ApplyReserveResponse = client.vc.v1.reserve.apply(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.vc.v1.reserve.apply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)
