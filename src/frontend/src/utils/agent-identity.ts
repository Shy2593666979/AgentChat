export const agentIcons = [
  { id: 'search', label: '搜索' }, { id: 'writing', label: '写作' },
  { id: 'chart', label: '数据' }, { id: 'code', label: '代码' },
  { id: 'book', label: '知识' }, { id: 'calendar', label: '日程' },
  { id: 'mail', label: '邮件' }, { id: 'weather', label: '天气' },
  { id: 'image', label: '图片' }, { id: 'package', label: '物流' },
  { id: 'bot', label: '助手' },
] as const
export const agentColors = [
  { id: 'blue', label: '蓝色', ink: '#176aff', tint: '#eaf3ff' },
  { id: 'purple', label: '紫色', ink: '#8950ef', tint: '#f2ecff' },
  { id: 'green', label: '绿色', ink: '#00b775', tint: '#e9fbf2' },
  { id: 'cyan', label: '青色', ink: '#00a8c4', tint: '#e8faff' },
  { id: 'orange', label: '橙色', ink: '#f79316', tint: '#fff3e5' },
  { id: 'pink', label: '粉色', ink: '#ed518a', tint: '#fff0f6' },
] as const
type IdentityInput = { name?: string; description?: string; logo_url?: string; knowledge_ids?: string[] }
const defaults: Record<string, string> = { search: 'blue', writing: 'purple', chart: 'orange', code: 'green', book: 'cyan', calendar: 'pink', bot: 'blue', mail: 'purple', weather: 'orange', image: 'pink', package: 'cyan' }
export function automaticIdentity(agent: IdentityInput, toolNames = '') {
  const text = `${agent.name || ''} ${agent.description || ''} ${toolNames}`.toLowerCase()
  const icon = /搜索|搜寻|研究|调研|检索|论文|search|research/.test(text) ? 'search'
    : /写作|文案|文章|writing|writer/.test(text) ? 'writing'
    : /编程|代码|开发|code|coding/.test(text) ? 'code'
    : /数据|统计|分析|data|analytics/.test(text) ? 'chart'
    : /日程|日历|提醒|calendar|schedule/.test(text) ? 'calendar'
    : /邮件|邮箱|mail/.test(text) ? 'mail'
    : /天气|weather/.test(text) ? 'weather'
    : /图片|绘图|文生图|image/.test(text) ? 'image'
    : /物流|快递|package/.test(text) ? 'package'
    : /知识|文档|问答|pdf|docx|knowledge/.test(text) || agent.knowledge_ids?.length ? 'book' : 'bot'
  return { icon, color: defaults[icon]! }
}
// 使用实际的静态 SVG 地址保存选择，兼容已有 logo_url 接口及对话头像。
export function identityUrl(icon: string, color: string, auto = false) {
  return `/ui/agent-icons/${icon}-${color}.svg${auto ? '?auto=1' : ''}`
}
export function parseIdentity(url = '') {
  const match = url.match(/\/ui\/agent-icons\/([a-z]+)-([a-z]+)\.svg(?:\?auto=1)?$/)
  if (!match || !agentIcons.some(i => i.id === match[1]) || !agentColors.some(c => c.id === match[2])) return null
  return { icon: match[1]!, color: match[2]!, auto: url.endsWith('?auto=1') }
}
export function isLegacyAgentLogo(url = '') {
  return !url || /\/icons\/(?:tools|agents?)\//i.test(url) || /(?:robot|bot)\.svg(?:\?|$)/i.test(url)
}
export function agentIdentity(agent: IdentityInput) {
  const stored = parseIdentity(agent.logo_url)
  const identity = stored || automaticIdentity(agent)
  return { ...identity, url: stored ? agent.logo_url! : isLegacyAgentLogo(agent.logo_url) ? identityUrl(identity.icon, identity.color) : agent.logo_url! }
}

// 目录 A 方案的默认主题；用户主动选择的图标颜色继续优先。
export function catalogAgentColor(agent: IdentityInput) {
  const stored = parseIdentity(agent.logo_url)
  if (stored && !stored.auto) return stored.color
  const icon = agentIdentity(agent).icon
  return ({search:'green',writing:'purple',chart:'orange',code:'purple',book:'purple',calendar:'cyan',mail:'pink',weather:'orange',image:'pink',package:'cyan',bot:'blue'} as Record<string,string>)[icon] || 'blue'
}
