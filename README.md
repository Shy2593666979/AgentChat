# 欢迎来到AgentChat

AgentChat 是一个开源的智能体交流与开发平台，更多的AIGC爱好者更好的了解Agent

## 项目应用

使用AgentChat 应用平台，可以构建各类更富的Agents供我们使用

默认提供的Agent

- 📧 根据我们想要的收件人以及邮件信息进行自动发送
- 🌏 帮助我们搜索更加有效的信息，更容易理解
- 🌥️ 帮助我们查给定地区的当前天气以及预报天气
- 📃 帮助我们查找一些顶尖论文
- 📦 根据快递公司和单号查找快递的信息

## 快速开始

### 配置文件

**1.配置LangFuse**

首先在`chat/config/langfuse_config.py` 中修改LangFuse的API KEY

默认的连接是LangFuse官网，如果连接不通的话也可以使用docker 将LangFuse部署在本地

**2.配置LLM**

在`chat/config/llm_config.py`中修改LLMs的API KEY 和 BASE_URL，目前仅支持function call的LLMs

例如：通义千问官网的qwen-plus...  openai的GPT-3.5....

**3.配置MySQL**

在`chat/config/service_config.py`中修改成自己的MySQL地址和Redis的地址

## 启动项目

**安装依赖**

`pip install -r requirement.txt`

**启动**

```
python main.py
```
