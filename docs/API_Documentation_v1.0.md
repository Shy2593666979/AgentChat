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
