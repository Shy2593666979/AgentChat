import json
import uuid

import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from typing import Optional
from pydantic import Field

from lark_mcp.mcp_tool.calendar.primary_calendar import get_primary_calendar
from lark_mcp.mcp_tool.utils.time import convert_timestamp


def update_calendar_event(
        calendar_id: str = Field(..., description="日历ID"),
        event_id: str = Field(..., description="日程事件ID"),
        user_id_type: str = Field(default="open_id", description="用户ID类型，默认为open_id"),
        summary: str = Field(..., description="需要更新的日程标题"),
        description: str = Field(None, description="需要更新的日程描述"),
        start_time: str = Field(..., description="需要更新的开始时间，格式YYYY-MM-DD HH:MM"),
        end_time: str = Field(..., description="需要更新的结束时间，格式YYYY-MM-DD HH:MM"),
        location_name: str = Field(None, description="需要更新的日程的会议位置"),
        location_address: str = Field(None, description="需要更新的日程的会议具体地点，如301会议室"),
        timezone: str = Field(None, description="需要更新的时区"),
        visibility: str = Field(None, description="需要更新的日程公开范围"),
        attendee_ability: str = Field(None, description="需要更新的参与者权限"),
        free_busy_status: str = Field(None, description="需要更新的日程占用的忙闲状态，新建日程默认为 busy"),
        recurrence: str = Field(None, description="需要更新的重复规则，遵循RRule规则，如FREQ=DAILY;INTERVAL=1"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参"),
):
    """更新飞书的日程事件信息，日程创建成功返回日程信息，失败返回错误信息"""
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .build()

    # 如果用户不指定日历ID，默认使用共享日历
    if not calendar_id:
        calendar_id = get_primary_calendar(app_id, app_secret)

    if not attendee_ability:
        attendee_ability = "can_see_others"

    # 将给的字符串时间转成时间戳
    start_timestamp  = convert_timestamp(start_time) if start_time else None
    end_timestamp = convert_timestamp(end_time) if end_time else None

    # 构造请求对象
    request: PatchCalendarEventRequest = PatchCalendarEventRequest.builder() \
        .event_id(event_id) \
        .calendar_id(calendar_id) \
        .user_id_type(user_id_type) \
        .request_body(CalendarEvent.builder()
                      .summary(summary)
                      .description(description)
                      .start_time(TimeInfo.builder()
                                  #.date(start_date) # 使用更精准的时间戳代表时间
                                  .timestamp(start_timestamp)
                                  .timezone(timezone)
                                  .build())
                      .end_time(TimeInfo.builder()
                                #.date(end_date) # 使用更精准的时间戳代表时间
                                .timestamp(end_timestamp)
                                .timezone(timezone)
                                .build())
                      .visibility(visibility)
                      .location(EventLocation.builder().name(location_name).address(location_address).build())
                      .attendee_ability(attendee_ability)
                      .free_busy_status(free_busy_status)
                      .recurrence(recurrence)
                      .build()) \
        .build()

    # 发起请求
    response: PatchCalendarEventResponse = client.calendar.v4.calendar_event.patch(request)

    # 处理失败返回
    if not response.success():
        error_msg = (
            f"client.calendar.v4.calendar_event.create failed, "
            f"code: {response.code}, "
            f"msg: {response.msg}, "
            f"log_id: {response.get_log_id()}, "
            f"resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        )
        lark.logger.error(error_msg)
        return error_msg

    # 基础事件信息处理
    update_calendar_event_message = lark.JSON.marshal(response.data, indent=4)
    lark.logger.info(update_calendar_event_message)

    # 返回组合结果
    return update_calendar_event_message