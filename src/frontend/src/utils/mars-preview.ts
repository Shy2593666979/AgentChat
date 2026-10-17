import { consumeMarsEvent, createMarsTask } from './mars-task';

// 仅供视觉验收，各示例不请求外部模型，也不创建真实资源。
export function marsPreview(kind = 2) {
  const examples: Record<number, { query: string; name: string; icon: string; steps: string[]; answer: string }> = {
    1: { query: '创建一个能查询天气的旅行助手', name: '构建智能体', icon: 'bot', steps: ['验证智能体名称与模型配置', '匹配天气工具与知识库', '智能体配置已创建'], answer: '# 旅行助手配置示例\n\n已整理以下智能体配置，供你查看展示效果。\n\n| 配置项 | 内容 |\n| --- | --- |\n| 名称 | 旅行助手 |\n| 能力 | 行程建议、天气查询 |\n| 使用方式 | 在智能体页开始对话 |\n\n[查看智能体页面](/agent)\n\n> 视觉演示，不会创建真实智能体。' },
    2: { query: '整理一份泰山游玩攻略，包括路线、交通与出行建议', name: '深度搜索', icon: 'search', steps: ['泰山景点介绍与旅游攻略', '泰山登山路线推荐：红门、天外村、桃花峪', '泰山门票与预约方式', '泰山交通：高铁、自驾与公交', '泰山日出与住宿准备'], answer: '# 泰山游玩攻略\n\n以下为你整理了泰山游玩攻略，涵盖经典路线、交通方式与出行准备，帮助你规划一次充实的泰山之旅。\n\n## 泰山简介\n\n泰山位于山东省泰安市，以自然景观与人文历史闻名。出发前可结合时间、体力和天气选择适合的路线。\n\n## 路线建议\n\n根据不同的时间与体力情况，可参考以下经典路线：\n\n1. **经典红门线路（体验完整）**\n   - **路线**：红门 → 中天门 → 南天门 → 玉皇顶\n   - **特点**：沿途景点较多，适合喜欢徒步的游客。\n   - **准备**：穿防滑鞋，携带饮水，按体力安排休息。\n2. **天外村路线（较为省力）**\n   - **路线**：天外村 → 中天门 → 索道或步行上山\n   - **特点**：可结合景区交通与索道，灵活调整行程。\n   - **准备**：提前了解当日交通与索道运行情况。\n3. **桃花峪路线（欣赏沿途风景）**\n   - **路线**：桃花峪 → 桃花源 → 索道或步行游览\n   - **特点**：适合希望结合自然风景安排游览的游客。\n\n## 门票与交通\n\n| 门票与预约 | 到达与出行 |\n| --- | --- |\n| 以景区当日公告为准 | 提前确认车站至景区入口的交通 |\n| 留意预约与开放时间 | 山区气温变化较快，准备保暖衣物 |\n\n> 视觉演示内容，不代表实时检索结果。' },
    3: { query: '生成一份 AI 日报，提供图片和下载文件', name: '生成 AI 日报', icon: 'file', steps: ['收集并整理 AI 新闻', '生成日报正文', '日报图片已生成'], answer: '# AI 日报\n\n日报支持正文、图片和文件链接一起展示。\n\n![日报排版演示](/ui/mars-daily-demo.svg)\n\n[查看 Markdown 文件示例](/ui/attachment-example.md)\n\n> 视觉演示，不代表今日真实新闻。' },
    4: { query: '检索知识库，汇总项目资料与待办事项', name: '检索知识库', icon: 'book', steps: ['读取可访问的知识库与文档', '检索项目资料与待办事项', '知识检索完成，正在整理报告'], answer: '# 项目资料汇总\n\n## 资料范围\n\n将相关文档整理为可阅读的摘要，保留表格与来源链接。\n\n| 主题 | 摘要 | 下一步 |\n| --- | --- | --- |\n| 产品设计 | 页面与交互规范 | 核对执行页细节 |\n| 开发进度 | 前后端事件协议 | 验证多工具输出 |\n\n[查看知识库](/knowledge)\n\n> 视觉演示，未读取真实文档。' },
  };
  const selected = examples[kind] || examples[4];
  const task = createMarsTask(kind === 5 ? '检索项目资料，再整理一份图文摘要' : selected.query);
  const addTool = (example: typeof selected, id: string) => {
    consumeMarsEvent(task, { type: 'tool_start', data: { id, label: example.name, icon: example.icon } });
    for (const message of example.steps) consumeMarsEvent(task, { type: 'progress_chunk', tool_id: id, data: { message, status: 'complete' } });
    consumeMarsEvent(task, { type: 'tool_end', data: { id, elapsed: 14 } });
  };
  if (kind === 5) { addTool(examples[4], 'preview-knowledge'); addTool(examples[3], 'preview-news'); }
  else addTool(selected, 'preview-tool');
  task.reasoning = '围绕需求选择合适的工具，整理可直接阅读和保存的输出。';
  task.answer = kind === 5 ? examples[4].answer + '\n\n## 图文摘要\n\n![图文摘要演示](/ui/mars-daily-demo.svg)' : selected.answer;
  task.state = 'done'; task.elapsed = kind === 5 ? 36 : 20;
  return task;
}
