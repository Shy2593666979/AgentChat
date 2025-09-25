import json
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from pydantic import Field

Permission_Lang_Map = {
    "私密": "private",
    "展示忙闲": "show_only_free_busy",
    "公开": "public"
}

def create_calendar(
    summary: str = Field(..., description="日历摘要"),
    description: str = Field("", description="日历描述（可选）"),
    permissions: str = Field("私密", description="日历权限，仅支持(私密，展示忙闲，公开)"),
    color: int = Field(-1, description="日历颜色, 其他值：通过RGB值的int32表示，客户端会映射到最接近的色板颜色"),
    summary_alias: str = Field(None, description="日历备注名（可选）"),
    app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
    app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
):
    """创建共享日历，成功返回共享日历信息，失败返回报错信息"""

    # 中文映射成英文方便提参
    permissions = Permission_Lang_Map.get(permissions, "private")

    # 初始化客户端
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求体
    request_body = Calendar.builder() \
        .summary(summary) \
        .description(description) \
        .permissions(permissions) \
        .color(color) \
        .summary_alias(summary_alias) \
        .build()

    # 构造请求对象
    request: CreateCalendarRequest = CreateCalendarRequest.builder() \
        .request_body(request_body) \
        .build()

    # 发起请求
    response: CreateCalendarResponse = client.calendar.v4.calendar.create(request)

    # 处理失败返回
    if not response.success():
        fail_message = f"client.calendar.v4.calendar.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        lark.logger.error(fail_message)
        return fail_message

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4)