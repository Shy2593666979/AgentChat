<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
![2a9a914f959cbe8efb9b1a5037ad866](https://github.com/user-attachments/assets/9a90b82e-1076-4b26-96ef-3da1eb3a04b0)

- [欢迎来到 智言平台](#%E6%AC%A2%E8%BF%8E%E6%9D%A5%E5%88%B0-%E6%99%BA%E8%A8%80%E5%B9%B3%E5%8F%B0)
  - [成果图](#%E6%88%90%E6%9E%9C%E5%9B%BE)
    - [智言平台首页](#%E6%99%BA%E8%A8%80%E5%B9%B3%E5%8F%B0%E9%A6%96%E9%A1%B5)
    - [使用GoogleAgent、WeatherAgent、DeliveryAgent、ArxivAgent](#%E4%BD%BF%E7%94%A8googleagentweatheragentdeliveryagentarxivagent)
    - [支持用户自定义工具](#%E6%94%AF%E6%8C%81%E7%94%A8%E6%88%B7%E8%87%AA%E5%AE%9A%E4%B9%89%E5%B7%A5%E5%85%B7)
    - [小彩蛋(先明说我是IKUN) 🤔🤔🤔](#%E5%B0%8F%E5%BD%A9%E8%9B%8B%E5%85%88%E6%98%8E%E8%AF%B4%E6%88%91%E6%98%AFikun-)
- [项目应用](#%E9%A1%B9%E7%9B%AE%E5%BA%94%E7%94%A8)
- [快速开始](#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)
    - [一、配置文件](#%E4%B8%80%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6)
    - [二、启动后端](#%E4%BA%8C%E5%90%AF%E5%8A%A8%E5%90%8E%E7%AB%AF)
    - [三、启动前端](#%E4%B8%89%E5%90%AF%E5%8A%A8%E5%89%8D%E7%AB%AF)
  - [使用Docker 快速启动](#%E4%BD%BF%E7%94%A8docker-%E5%BF%AB%E9%80%9F%E5%90%AF%E5%8A%A8)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# 欢迎来到 AgentChat

AgentChat 是一个开源的智能体交流与开发平台，让更多的AIGC爱好者更好的了解Agent

## 成果图（V1.0， V2.0前端页面还没做好）
### 智言平台首页
![1725542910516](https://github.com/user-attachments/assets/9036192a-8d19-4c3f-86d9-98f2b057b6b3)

### 使用GoogleAgent、WeatherAgent、DeliveryAgent、ArxivAgent

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/932a0263-6949-413c-ae06-2afd92b92eef" alt="Image 1" width="1000"></td>
    <td><img src="https://github.com/user-attachments/assets/263870c0-f6a9-437c-a289-13763804b3ee" alt="Image 2" width="1000"></td>
  </tr>
</table>

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/1b295f35-f122-400c-8351-e5b3e3f65663" alt="Image 1" width="1000"></td>
    <td><img src="https://github.com/user-attachments/assets/059d4711-10af-40ea-8707-fd9967aa26a9" alt="Image 3" width="1000"></td>
  </tr>
</table>



### 支持用户自定义工具
用户需要输入openai 的参数格式，以及自定义代码（显得比较不是那么智能，后续会更改😔）
![1725543216627](https://github.com/user-attachments/assets/beb54a14-521a-41fd-9941-ad82262276ff)

### 小彩蛋(先明说我是IKUN) 🤔🤔🤔
加载图标：

![image](https://github.com/user-attachments/assets/3e4201c2-0f2b-4f9f-906c-a09e49aea9b8)

![kunkun](https://github.com/user-attachments/assets/16e8a37b-32c2-4124-b6cf-151335482937)


# 项目应用

使用 智言应用平台，可以构建各类更丰富的Agents供我们使用

默认提供的Agent

- 📧 根据我们想要的收件人以及邮件信息进行自动发送
- 🌏 帮助我们搜索更加有效的信息，更容易理解
- 🌥️ 帮助我们查给定地区的当前天气以及预报天气
- 📃 帮助我们查找一些顶尖论文
- 📦 根据快递公司和单号查找快递的信息
- 📂 根据用户提供的文档路径进行加载到知识库进行检索，支持.pdf .docx .xlsx .md .txt文档加载

# 快速开始

### 一、配置文件

**1.配置LangFuse**

首先在`chat/config/langfuse_config.py` 中修改LangFuse的API KEY

默认的连接是LangFuse官网，如果连接不通的话也可以使用docker 将LangFuse部署在本地

**2.配置LLM**

在`chat/config/llm_config.py`中修改LLMs的API KEY 和 BASE_URL，目前仅支持function call的LLMs

例如：通义千问官网的qwen-plus...  openai的GPT-3.5....

**3.配置MySQL**

在`chat/config/service_config.py`中修改成自己的MySQL地址和Redis的地址

### 二、启动后端

**1.安装依赖**

`pip install -r requirement.txt`

**2.启动**

在DeepSleep\src\backend目录下执行启动命令

```shell
uvicorn agentchat.main:app --port 7860 --host 0.0.0.0
```

### 三、启动前端

**1.进入到前端的文件夹下**

**2.下载依赖文件**
```shell
npm install
```
**3.启动前端服务**
```
npm run dev
```

## 使用Docker 快速启动

使用Docker的话就少了配置MySQL数据库步骤

**1.进入docker文件**

**2.执行Docker命令**

`docker-compose up --build `

**3.用上述启动后端、前端的方式进行启动整体项目**

**4.更新配置文件后重新启动**

## 启动事项

## 启动需要注意事项

因为fast-jwt-auth版本很多年没有再更新，所以其中使用的pydantic版本较低。
但是像该项目中的Langchain、MCP都需要升级pydantic >= 2。
当前也没什么好的办法，所以建议将虚拟环境中的fastapi-jwt-auth的SDK中config.py文件进行更改

例如在我电脑中，需要更改的文件就是

`D:\conda\envs\agentchat\Lib\site-packages\fastapi_jwt_auth\config.py` 

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

## 向量库安装

https://milvus.io/docs/zh/install_standalone-windows.md

## Rerank模型示例

https://help.aliyun.com/zh/model-studio/text-rerank-api

## Embedding模型示例

https://help.aliyun.com/zh/model-studio/embedding-interfaces-compatible-with-openai