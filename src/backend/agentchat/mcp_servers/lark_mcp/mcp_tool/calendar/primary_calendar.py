import json

import lark_oapi as lark
from lark_oapi.api.calendar.v4 import PrimaryCalendarRequest, PrimaryCalendarResponse


# 该函数不接入MCP，是其他MCP工具调用该函数所使用
def get_primary_calendar(app_id: str, app_secret: str):
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .build()

    # 构造请求对象
    request: PrimaryCalendarRequest = PrimaryCalendarRequest.builder() \
        .user_id_type("open_id") \
        .build()

    # 发起请求
    response: PrimaryCalendarResponse = client.calendar.v4.calendar.primary(request)

    # 处理失败返回
    if not response.success():
        error_message = f"client.calendar.v4.calendar.primary failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(error_message)
        raise ValueError(error_message)

    # 处理业务结果
    lark.logger.info("获取公共日历的结果：")
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    # return lark.JSON.marshal(response.data, indent=4)


    marshal_resp = json.loads(lark.JSON.marshal(response.data.calendars, indent=4))

    # 获取一个公共的日历
    for res in marshal_resp:
        if res["calendar"]["type"] == "primary":
            return res["calendar"]["calendar_id"]

    return None