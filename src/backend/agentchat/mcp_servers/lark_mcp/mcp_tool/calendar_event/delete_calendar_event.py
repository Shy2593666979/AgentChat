import json
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from pydantic import Field
from typing import Optional, Literal

from lark_mcp.mcp_tool.calendar.primary_calendar import get_primary_calendar


def delete_calendar_event(
    calendar_id: str = Field(..., description="日历ID"),
    event_id: str = Field(..., description="日程事件ID"),
    need_notification: str = Field("true", description="是否通知参与者：true-通知，false-不通知"),
    app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
    app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """删除指定的日程事件，成功返回删除成功信息，失败返回报错信息"""
    # 初始化客户端
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 如果用户不指定日历ID，默认使用共享日历
    if not calendar_id:
        calendar_id = get_primary_calendar(app_id, app_secret)

    # 构造请求对象
    request: DeleteCalendarEventRequest = DeleteCalendarEventRequest.builder() \
        .calendar_id(calendar_id) \
        .event_id(event_id) \
        .need_notification(need_notification) \
        .build()

    # 发起请求
    response: DeleteCalendarEventResponse = client.calendar.v4.calendar_event.delete(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.calendar.v4.calendar_event.delete failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.raw.content, indent=4))
    return lark.JSON.marshal(response.raw.content, indent=4)