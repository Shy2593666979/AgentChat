# README 素材

截图由运行中的本地前端采集，只包含应用内容。

| 文件 | 内容 |
| --- | --- |
| `cover.jpg` | 当前机器人与小写 agentchat 字标的项目封面 |
| `cover-source.html` | 封面源文件，复用项目现有字体和品牌图片 |
| `login.jpg` | Mingguang 登录入口，密码为空 |

## 演示数据

在仓库根目录执行：

```powershell
python scripts/seed_readme_demo.py --user Mingguang
python scripts/seed_readme_demo.py --user Mingguang --apply
```

仅支持本地 SQLite，账号必须已存在。脚本写入前将数据库备份到被 Git 忽略的 `.runtime/`，不修改密码，不覆盖已有业务记录。重复执行更新同一批带独立 ID 的演示记录。演示模型密钥为空，不能用于真实调用；会话内容和用量统计为虚构展示数据。

## 当前页面与视频

- `explore.jpg`：探索首页。
- `conversation.jpg`：演示会话。
- `dashboard.jpg`：近七日统计。
- `models.jpg`：截取六家厂商各一款的模型表格区域。
- `agents.jpg`：我的智能体。
- `tools.jpg`、`skills.jpg`、`mcp.jpg`、`knowledge.jpg`：能力管理页面。
- `mars.jpg`：本次真实任务的完成状态。
- `mars-example.mp4`：当前 README 唯一使用的演示视频，来自用户提供的剪辑成片。文件原样复制，未重新编码；约 21.37 秒，1464×720，30 fps，H.264 / AAC。
- `mars-example-poster.jpg`：从该成片第 1 秒提取的网页播放器封面。
- `recording.json`：当前剪辑视频的来源及媒体参数。
- `index.html`：网页播放器与视频下载入口。

README 与播放器均指向同一剪辑成片，不再使用旧原速版本。原始录制素材保留在未跟踪的 `.runtime/` 中。

探索任务录屏使用实际请求：

> 中国四大古都的影响力对比，给我做一份这四个城市的旅游攻略。

演示展示真实任务执行过程。当前视频已由用户剪辑，README 不再将其标注为“原速”或“无剪切”。README 使用 GitHub 视频附件地址独占一段，渲染为支持播放、进度拖动、音量和全屏的内嵌播放器；保留仓库中的 MP4 作为原文件及网页播放器的视频源。

GitHub 视频附件：https://github.com/user-attachments/assets/640650f3-4134-452a-9d17-6f850dabe95f
