import json
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from pydantic import Field
from typing import Optional


def get_calendars_list(
        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """获取日历列表，成功返回日历列表，失败返回报错信息"""
    page_size = 100
    # 初始化客户端
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request_builder = ListCalendarRequest.builder().page_size(page_size)

    request: ListCalendarRequest = request_builder.build()

    # 发起请求
    response: ListCalendarResponse = client.calendar.v4.calendar.list(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.calendar.v4.calendar.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    return lark.JSON.marshal(response.data, indent=4)

    # # 对超过2000字符的工具进行特殊处理
    # max_return_char = 2000
    #
    # current_calendar = []
    # for calendar_info in response.data.calendar_list:
    #     if len(current_calendar) + len(str(calendar_info)) > max_return_char:
    #         current_calendar.append("上下文长度超出限制，仅展示部分日历信息")
    #         break
    #     else:
    #         current_calendar.append(calendar_info)
    # return str(current_calendar)
