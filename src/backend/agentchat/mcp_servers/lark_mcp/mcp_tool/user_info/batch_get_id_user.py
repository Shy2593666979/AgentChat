import json
import lark_oapi as lark
from lark_oapi.api.contact.v3 import *
from pydantic import Field, BaseModel


def get_user_info_request(user_id_type: str = Field(default="open_id", description="用户ID类型，默认为 open_id"),
                        emails: List[str] = Field(None, description="列表的形式，最多50个邮箱，不支持企业邮箱，与 mobiles 独立查询"),
                        mobiles: List[str] = Field(None,
                                                   description="列表的形式，最多50个手机号，海外需带国家代码 +xxx，与 emails 独立查询"),
                        include_resigned: bool = Field(True, description="是否包含已离职员工，true/false"),
                        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
                        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")):
    """根据用户的邮箱或者手机号查找用户的信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: BatchGetIdUserRequest = BatchGetIdUserRequest.builder() \
        .user_id_type(user_id_type) \
        .request_body(BatchGetIdUserRequestBody.builder()
                      .emails(emails)
                      .mobiles(mobiles)
                      .include_resigned(include_resigned)
                      .build()) \
        .build()

    # 发起请求
    response: BatchGetIdUserResponse = client.contact.v3.user.batch_get_id(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.contact.v3.user.batch_get_id failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return f"client.contact.v3.user.batch_get_id failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return str(lark.JSON.marshal(response.data, indent=4))
