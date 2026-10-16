// 只按工具名称判断图标，避免描述中的关键词误判类型。
export function toolVisual(name: string) {
  const text = name.toLowerCase();
  if (/邮件|mail/.test(text)) return { kind: 'mail', theme: 'blue', tag: '办公协作' };
  if (/天气|weather/.test(text)) return { kind: 'weather', theme: 'cyan', tag: '生活服务' };
  if (/论文|arxiv|paper/.test(text)) return { kind: 'research', theme: 'violet', tag: '学术检索' };
  if (/物流|快递|delivery|express/.test(text)) return { kind: 'delivery', theme: 'orange', tag: '生活服务' };
  if (/图片|图像|文生图|image|绘图/.test(text)) return { kind: 'image', theme: 'rose', tag: '内容创作' };
  if (/代码|code|python|执行|开发/.test(text)) return { kind: 'code', theme: 'purple', tag: '开发工具' };
  if (/数据|database|sql|查询/.test(text)) return { kind: 'database', theme: 'orange', tag: '数据工具' };
  if (/文档|文件|pdf|docx|document|convert/.test(text)) return { kind: 'document', theme: 'green', tag: '文档处理' };
  if (/知识|knowledge/.test(text)) return { kind: 'book', theme: 'violet', tag: '知识管理' };
  if (/搜索|search|web/.test(text)) return { kind: 'globe', theme: 'blue', tag: '信息检索' };
  return { kind: 'custom', theme: 'blue', tag: '扩展工具' };
}
