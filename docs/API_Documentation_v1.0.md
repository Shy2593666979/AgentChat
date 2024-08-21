
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
|dialogId|对话ID|string|是||
|userInput|用户输入|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

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
|data|返回的数据|dict|是|{"dialogId": "xx1s31sfsx00sfwq...."}|

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
|data|返回的数据|List[dict]|是|{"dialogId": "xx1ss131xxxsswq....", "name": "你好xxxx", "agent": "Google搜索"}|

## MessageLikeCreate

### 主要功能
用户点击点赞功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库

### 请求方式
- POST
### 请求地址

`http://127.0.0.1:8880/message/like`
### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|userInput|用户输入|string|是||
|agentOutput|agent回复的消息|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||

## MessageLikeCreate

### 主要功能
用户点击拉踩功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库

### 请求方式
- POST
### 请求地址

`http://127.0.0.1:8880/message/down`
### 所需参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|userInput|用户输入|string|是||
|agentOutput|agent回复的消息|string|是||

### 返回参数

|参数名|中文|数据类型|是否必须|备注|
|---|---|---|---|---|
|code|状态码|int|是||
|message|请求信息|string|是||
|data|返回的数据|string|是||
