import json

import lark_oapi as lark
from lark_oapi.api.contact.v3 import *
from pydantic import Field, BaseModel
from typing import Literal


def batch_get_user_info(user_id_type: str = Field(default="open_id", description="用户ID类型，默认为 open_id"),
                        emails: List[str] = Field(None,
                                                  description="列表的形式，最多50个邮箱，不支持企业邮箱，与 mobiles 独立查询"),
                        mobiles: List[str] = Field(None,
                                                   description="列表的形式，最多50个手机号，海外需带国家代码 +xxx，与 emails 独立查询"),
                        include_resigned: bool = Field(True, description="是否包含已离职员工，true/false"),
                        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
                        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")):
    """根据用户的邮箱或者手机号查找用户的信息(包含用户ID)"""
    user_id_type = "open_id"

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

    # 获取根据手机号或者邮箱查到的用户ID
    user_ids = [user_info.user_id for user_info in response.data.user_list]

    # 根据用户ID查找到用户的更多信息
    user_messages = get_user_info_by_id(user_ids, user_id_type, "open_department_id", app_id, app_secret)

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return lark.JSON.marshal(response.data, indent=4) + user_messages


# 根据用户ID查看用户的具体信息
def get_user_info_by_id(user_ids: List[str] = Field(...,
                                                    description="用户ID列表，ID类型与 user_id_type 参数一致。单次请求最多支持50个用户ID。"),
                        user_id_type: str = Field(default="open_id",
                                                  description="用户ID类型，可选值：open_id、union_id、user_id。"),
                        department_id_type: str = Field(default="open_department_id",
                                                        description="部门ID类型，可选值：open_department_id、department_id。"),
                        app_id: str = Field(None, description="应用唯一标识，默认从用户配置中自动获取，无需额外传参"),
                        app_secret: str = Field(None, description="应用密钥，默认从用户配置中自动获取，无需额外传参")
                        ):
    """根据用户ID可以批量获取用户的具体信息"""
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: BatchUserRequest = BatchUserRequest.builder() \
        .user_id_type(user_id_type) \
        .department_id_type(department_id_type) \
        .user_ids(user_ids) \
        .build()

    # 发起请求
    response: BatchUserResponse = client.contact.v3.user.batch(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.contact.v3.user.batch failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return str(
            f"client.contact.v3.user.batch failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    return lark.JSON.marshal(response.data, indent=4)
