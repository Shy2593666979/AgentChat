export function skillTags(name: string, detail = false): string[] {
  if (/研究|报告/.test(name)) return detail ? ['研究分析', '信息检索', '报告生成', '多领域'] : ['研究', '分析', '报告'];
  if (/数据|分析/.test(name)) return ['数据', '分析', '可视化'];
  if (/产品|文档/.test(name)) return ['产品', '文档', '需求'];
  if (/代码|审查|开发/.test(name)) return ['代码', '审查', '优化'];
  if (/邮件|mail/i.test(name)) return ['邮件', '沟通', '写作'];
  if (/知识|整理/.test(name)) return ['知识', '整理', '总结'];
  return ['技能', '工作流'];
}
