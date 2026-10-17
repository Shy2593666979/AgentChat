export function resourceVisual(name: string, skill = false) {
  const text = name.toLowerCase()
  if (!skill && /搜索|search/.test(text)) return { icon:'globe', kind:'globe', theme:'blue', tag:'信息检索' }
  if (/数据|database|sql|analytics/.test(text)) return { icon:'database', kind:'analytics', theme:skill ? 'green' : 'orange', tag:'数据工具' }
  if (/代码|code|python|开发/.test(text)) return { icon:'code', kind:'coding', theme:'purple', tag:'开发工具' }
  if (/邮件|mail|email/.test(text)) return { icon:'mail', kind:'mail', theme:skill ? 'rose' : 'blue', tag:'办公协作' }
  if (/图片|image|绘图/.test(text)) return { icon:'image', kind:'image', theme:'rose', tag:'内容创作' }
  if (/产品|product/.test(text)) return { icon:'file', kind:'enterprise', theme:'orange', tag:'文档处理' }
  if (/知识|knowledge/.test(text)) return { icon:'book', kind:'knowledge', theme:'violet', tag:'知识管理' }
  if (/文件|文档|document|file|pdf/.test(text)) return { icon:'file', kind:'document', theme:'green', tag:'文档处理' }
  if (/浏览器|browser/.test(text)) return { icon:'browser', kind:'browser', theme:'orange', tag:'浏览器' }
  return { icon:skill ? 'file' : 'globe', kind:skill ? 'document' : 'globe', theme:'blue', tag:/搜索|search|web/.test(text) ? '信息检索' : '工具' }
}
export function responseError(error: any, fallback: string) {
  const detail = error?.response?.data?.detail
  return typeof detail === 'string' ? detail : error?.message || fallback
}
