import json
import uuid

import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from pydantic import Field
from lark_mcp.mcp_tool.calendar.primary_calendar import get_primary_calendar
from lark_mcp.mcp_tool.calendar_event.append_calendar_event_attendees import append_calendar_event_attendee
from lark_mcp.mcp_tool.utils.time import convert_timestamp


def create_calendar_event(
        user_id_type: str = Field(default="open_id",
                                            description="用户ID类型，默认值为open_id"),
        calendar_id: str = Field(..., description="日历ID"),
        summary: str = Field(..., description="日程标题"),
        description: str = Field(..., description="日程描述"),
        need_notification: bool = Field(True, description="更新日程时，是否给日程参与人发送通知"),
        start_time: str = Field(..., description="开始时间，格式YYYY-MM-DD HH:MM"),
        end_time: str = Field(..., description="结束时间，格式YYYY-MM-DD HH:MM"),
        location_name: str = Field(None, description="日程的会议位置"),
        location_address: str = Field(None, description="日程的会议具体地点，如301会议室"),
        attendees: List[str] = Field(None, description="参会者列表，每个元素需包含用户的open_id"),
        timezone: str = Field("Asia/Shanghai", description="时区"),
        visibility: str = Field("default", description="日程公开范围"),
        attendee_ability: str = Field("can_see_others", description="参与者权限"),
        free_busy_status: str = Field("busy", description="日程占用的忙闲状态，新建日程默认为 busy"),
        recurrence: str = Field("FREQ=DAILY;INTERVAL=1", description="遵循日历RRule重复规则，如FREQ=DAILY;INTERVAL=1"),
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参"),
):
    """创建飞书日程事件，日程创建成功返回日程信息，失败返回错误信息"""
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 获取一个公共日历
    # try:
    #     calendar_id = get_primary_calendar(app_id, app_secret)
    # except Exception as err:
    #     error_msg = str(err)
    #     lark.logger.error(error_msg)
    #     return error_msg


    # 将给的字符串时间转成时间戳
    start_timestamp = convert_timestamp(start_time)
    end_timestamp = convert_timestamp(end_time)


    # 构造请求对象
    request: CreateCalendarEventRequest = CreateCalendarEventRequest.builder() \
        .calendar_id(calendar_id) \
        .idempotency_key(uuid.uuid4().hex) \
        .user_id_type(user_id_type) \
        .request_body(CalendarEvent.builder()
                      .summary(summary)
                      .description(description)
                      .need_notification(need_notification)
                      .start_time(TimeInfo.builder()
                                  #.date(start_date) # 使用更精准的时间戳代表时间
                                  .timestamp(start_timestamp)
                                  .timezone(timezone)
                                  .build())
                      .end_time(TimeInfo.builder()
                                #.date(end_date)  # 使用更精准的时间戳代表时间
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
    response: CreateCalendarEventResponse = client.calendar.v4.calendar_event.create(request)

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
    calendar_event_message = lark.JSON.marshal(response.data, indent=4)
    lark.logger.info(calendar_event_message)

    # 参会人处理（如果有参会人）
    event_attendee_message = ""
    if attendees:
        try:
            event_id = response.data.event.event_id
            attendee_response = append_calendar_event_attendee(
                app_id=app_id,
                app_secret=app_secret,
                event_id=event_id,
                calendar_id=calendar_id,
                user_id_type=user_id_type,
                attendees=attendees,
                need_notification=need_notification
            )
            event_attendee_message = lark.JSON.marshal(attendee_response, indent=4)
            lark.logger.info(event_attendee_message)
        except Exception as err:
            error_msg = f"添加参会人失败: {str(err)}"
            lark.logger.error(error_msg)
            # 这里根据业务需求决定：是忽略错误继续返回基础事件信息，还是直接返回错误
            # 当前选择忽略错误继续返回，可根据实际情况调整
            # return error_msg

    # 返回组合结果
    return calendar_event_message + event_attendee_message if event_attendee_message else calendar_event_message

if __name__ == "__main__":
    response = create_calendar_event(app_id="cli_a834d157e139d00d", app_secret="C8B0fhx7Pqpll9gB0zsuThhxinaaq47G", summary="测试22222", description="xxxxxxxxxxxxx",
                          start_time="2025-09-19 12:00", end_time="2025-09-20 14:00",
    user_id_type = "open_id",
    need_notification = True,
    location_name = None,
    location_address = None,
    calendar_id="feishu.cn_vjYauAuYvKD2Mx5ISTtRhd@group.calendar.feishu.cn",
    attendees = ["ou_809896f3ed229a09e20474c4d1451d32"],
    timezone = "Asia/Shanghai",
    visibility = "default",
    attendee_ability = "can_see_others",
    free_busy_status = "busy",
    recurrence = "FREQ=DAILY")

    print(response)