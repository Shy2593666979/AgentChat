# 欢迎来到 智言平台

智言平台 是一个开源的智能体交流与开发平台，让更多的AIGC爱好者更好的了解Agent

## 成果图
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


## 项目应用

使用 智言应用平台，可以构建各类更丰富的Agents供我们使用

默认提供的Agent

- 📧 根据我们想要的收件人以及邮件信息进行自动发送
- 🌏 帮助我们搜索更加有效的信息，更容易理解
- 🌥️ 帮助我们查给定地区的当前天气以及预报天气
- 📃 帮助我们查找一些顶尖论文
- 📦 根据快递公司和单号查找快递的信息
- 📂 根据用户提供的文档路径进行加载到知识库进行检索，支持.pdf .docx .xlsx .md .txt文档加载

## 快速开始

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

```
python main.py
```

### 三、启动前端

**1.进入到前端的文件夹下**

**2.下载依赖文件**
```shell
npm i
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

