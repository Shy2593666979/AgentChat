# 对话

## Chat

### 主要功能

主要负责的是与LLM进行对话的接口，LLM输入需要流式输出

### 请求方式

- POST

### 请求地址
`http://127.0.0.1:8880/chat`

### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|dialog_id|对话ID|string|是||
|user_input|用户输入|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

# 对话窗口

## DialogCreate

### 主要功能

主要创建对话窗口的信息

### 请求方式
- POST

### 请求地址
`http://127.0.0.1:8880/dialog`

### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|name|对话名称|string|是||
|agent|选的agent助手|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|dict|是|{"dialog_id": "xx1s31sfsx00sfwq...."}|

## DialogList

### 主要功能

主要获得对话列表的功能

### 请求方式
- GET

### 请求地址
`http://127.0.0.1:8880/dialog/list`

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|List[dict]|是|{"dialog_id": "xx1ss131xxxsswq....", "name": "你好xxxx", "agent": "Google搜索"}|

# Agent管理

## AgentCreate

### 主要功能
用户可自定义创建Agent，需要将所需的参数返回给后端保存到数据库当中

### 请求方式

- POST

### 请求地址

`http://127.0.0.1:8880/agent`

### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|name|Agent名字|string|是|要求必须是大小写字母、数字组成，这个后端判断并返回|
|description|Agent描述|string|是||
|parameter|Agent参数|string|是|输入的参数是openai格式，希望提供用户的输入框是适合json格式的文本|
|code|Agent执行代码|string|是|code 必须是可执行的函数|
|logoFile|Agent logo|File|是||

ps: Agent 这些增删改查都是 使用**FormData**  ----因为都跟上传文件有关,使用Form更合适

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

## AgentList

### 主要功能
获取Agents 的列表信息

### 请求方式

- GET

### 请求地址

`http://127.0.0.1:8880/agent`

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|List[Dict]|是|{id: "xxsswq", name: "WeatherAgent", description: "获取当地的预报天气", parameter: ".....", is_custom: True, create_time: "2024-8-23-16-43"}   is_custom表示是否是自定义|

## AgentDelete

### 主要功能
删除Agent

### 请求方式

- Delete

### 请求地址

`http://127.0.0.1:8880/agent`

### 所需参数
|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|id|Agent的id|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

## AgentUpdate

### 主要功能

修改Agent 的信息

### 请求方式
- PUT

### 请求地址

`http://127.0.0.1:8880/agent`

### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|name|Agent名字|string|是|要求必须是大小写字母、数字，这个后端判断并返回|
|description|Agent描述|string|是||
|parameter|Agent参数|string|是|输入的参数是openai格式，希望提供用户的输入框是适合json格式的文本|
|code|Agent执行代码|string|是|code 必须是可执行的函数|
|logoFile|Agent logo|File|是||

ps: Agent 这些增删改查都是 使用**FormData**  ----因为都跟上传文件有关,使用Form更合适

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

# 每条信息

## MessageLikeCreate

### 主要功能
用户点击点赞功能，需要前端将user_input和agent_output 返回给后端进行存入数据库

### 请求方式
- POST
### 请求地址

`http://127.0.0.1:8880/message/like`
### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|user_input|用户输入|string|是||
|agent_output|agent回复的消息|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

## MessageLikeCreate

### 主要功能
用户点击拉踩功能，需要前端将user_input和agent_output 返回给后端进行存入数据库

### 请求方式
- POST
### 请求地址

`http://127.0.0.1:8880/message/down`
### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|user_input|用户输入|string|是||
|agent_output|agent回复的消息|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

## 启动需要注意事项

因为fast-jwt-auth版本很多年没有再更新，所以其中使用的pydantic版本较低。
但是像该项目中的Langchain、MCP都需要升级pydantic >= 2。
当前也没什么好的办法，所以建议将虚拟环境中的fastapi-jwt-auth的SDK中config.py文件进行更改

例如在我电脑中，需要更改的文件就是

`D:\conda\envs\deepsleep\Lib\site-packages\fastapi_jwt_auth\config.py` 

更改成以下代码：
```python
from datetime import timedelta
from typing import Optional, Union, Sequence, List
from pydantic import (
    BaseModel,
    validator,
    StrictBool,
    StrictInt,
    StrictStr
)

class LoadConfig(BaseModel):
    authjwt_token_location: Optional[List[StrictStr]] = ['headers']
    authjwt_secret_key: Optional[StrictStr] = None
    authjwt_public_key: Optional[StrictStr] = None
    authjwt_private_key: Optional[StrictStr] = None
    authjwt_algorithm: Optional[StrictStr] = "HS256"
    authjwt_decode_algorithms: Optional[List[StrictStr]] = None
    authjwt_decode_leeway: Optional[Union[StrictInt,timedelta]] = 0
    authjwt_encode_issuer: Optional[StrictStr] = None
    authjwt_decode_issuer: Optional[StrictStr] = None
    authjwt_decode_audience: Optional[Union[StrictStr,Sequence[StrictStr]]] = None
    authjwt_denylist_enabled: Optional[StrictBool] = False
    authjwt_denylist_token_checks: Optional[List[StrictStr]] = ['access','refresh']
    authjwt_header_name: Optional[StrictStr] = "Authorization"
    authjwt_header_type: Optional[StrictStr] = "Bearer"
    authjwt_access_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(minutes=15)
    authjwt_refresh_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(days=30)
    # # option for create cookies
    authjwt_access_cookie_key: Optional[StrictStr] = "access_token_cookie"
    authjwt_refresh_cookie_key: Optional[StrictStr] = "refresh_token_cookie"
    authjwt_access_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_cookie_path: Optional[StrictStr] = "/"
    authjwt_cookie_max_age: Optional[StrictInt] = None
    authjwt_cookie_domain: Optional[StrictStr] = None
    authjwt_cookie_secure: Optional[StrictBool] = False
    authjwt_cookie_samesite: Optional[StrictStr] = None
    # # option for double submit csrf protection
    authjwt_cookie_csrf_protect: Optional[StrictBool] = True
    authjwt_access_csrf_cookie_key: Optional[StrictStr] = "csrf_access_token"
    authjwt_refresh_csrf_cookie_key: Optional[StrictStr] = "csrf_refresh_token"
    authjwt_access_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_access_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_refresh_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_csrf_methods: Optional[List[StrictStr]] = ['POST','PUT','PATCH','DELETE']

    @validator('authjwt_access_token_expires')
    def validate_access_token_expires(cls, v):
        if v is True:
            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
        return v

    @validator('authjwt_refresh_token_expires')
    def validate_refresh_token_expires(cls, v):
        if v is True:
            raise ValueError("The 'authjwt_refresh_token_expires' only accept value False (bool)")
        return v

    @validator('authjwt_denylist_token_checks', each_item=True)
    def validate_denylist_token_checks(cls, v):
        if v not in ['access','refresh']:
            raise ValueError("The 'authjwt_denylist_token_checks' must be between 'access' or 'refresh'")
        return v

    @validator('authjwt_token_location', each_item=True)
    def validate_token_location(cls, v):
        if v not in ['headers','cookies']:
            raise ValueError("The 'authjwt_token_location' must be between 'headers' or 'cookies'")
        return v

    @validator('authjwt_cookie_samesite')
    def validate_cookie_samesite(cls, v):
        if v not in ['strict','lax','none']:
            raise ValueError("The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none'")
        return v

    @validator('authjwt_csrf_methods', each_item=True)
    def validate_csrf_methods(cls, v):
        if v.upper() not in ["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]:
            raise ValueError("The 'authjwt_csrf_methods' must be between http request methods")
        return v.upper()

    class Config:
        str_min_length = 1
        str_strip_whitespace = True
```

## 向量库

https://milvus.io/docs/zh/install_standalone-windows.md