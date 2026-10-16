# 默认 Skill

启动时自动载入六个默认技能：研究报告、数据分析、产品文档、代码审查、邮件写作、知识整理。使用现有 `agent_skill` 表，不新增数据库表，不调用模型生成工具名称。

- 清单：`src/backend/agentchat/config/default_skills.json`。
- 文件：`src/backend/agentchat/config/skills/<key>/SKILL.md`。
- 每个目录还包含输出模板、复核清单与 `SOURCES.md`，共四个真实文件。
- 固定 ID 由配置标识派生；工具名称在清单中固定配置。

技能内容是参考公开工作流方向、为 AgentChat 独立编写的中文版本，并非上游完整安装。参考来源分别为 Composio 的 content-research-writer、CSV Data Summarizer、Anthropic 的 doc-coauthoring、Sentry 的 code-review、Anthropic 的 internal-comms、OpenAI 的 notion-knowledge-capture；具体链接在各目录的 `SOURCES.md` 中。

系统用户下的默认技能只作为模板，注册时为每位用户创建独立 ID 的副本。用户在 Skill 列表查看、编辑和选择自己的记录，不影响其他用户。列表入口为 `/agent-skill`，页面仅加载真实数据，不再提供示例预览。详见[用户私有资源](private-resources.md)。

加载只补齐缺失的系统模板。用户初始化完成后，再次启动不会重复新增、覆盖个人修改或补回已删除的默认技能。新增模板不自动下发到已初始化账号。

当前 Skill 子智能体只有读取与列举技能文件的工具。因此技能用于处理对话中实际提供的材料，不会自动联网、执行代码、发送邮件或写入外部知识库。数据分析可以给出代码建议，但不能声称已执行或生成图表。使用完整外部工具能力需要另行扩展子智能体工具配置。
