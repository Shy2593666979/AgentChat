import json
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from pydantic import Field
from typing import Optional

def get_calendar_info(
    calendar_id: str = Field(..., description="日历ID（必填），用于指定要获取的日历"),
    app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
    app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """获取指定的日历信息，成功返回日历信息，失败返回报错信息"""
    # 初始化客户端
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: GetCalendarRequest = GetCalendarRequest.builder() \
        .calendar_id(calendar_id) \
        .build()

    # 发起请求
    response: GetCalendarResponse = client.calendar.v4.calendar.get(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.calendar.v4.calendar.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)