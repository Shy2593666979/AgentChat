export function formatDataDate(value: string | undefined, withTime = true) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  const pad = (n: number) => String(n).padStart(2, '0')
  const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  return withTime ? `${day} ${pad(date.getHours())}:${pad(date.getMinutes())}` : day
}
export function safeResourceUrl(value: string | undefined) {
  if (!value) return ''
  try {
    const url = new URL(value, window.location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch { return '' }
}
export function storedSizeBytes(value: string | number) {
  if (typeof value === 'number') return Math.max(0, value)
  const match = String(value || '').match(/^\s*(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)\s*$/i)
  return match ? Number(match[1]) * 1024 ** ['B', 'KB', 'MB', 'GB', 'TB'].indexOf(match[2].toUpperCase()) : 0
}
export function readableBytes(value: number) {
  if (!Number.isFinite(value) || value < 0) return '—'
  if (!value) return '0 B'
  const exponent = Math.min(4, Math.floor(Math.log(value) / Math.log(1024)))
  return `${Number((value / 1024 ** exponent).toFixed(1))} ${['B', 'KB', 'MB', 'GB', 'TB'][exponent]}`
}
export function fileState(value: unknown) {
  const raw = String(value || '')
  if (/success|complete|完成|✅/i.test(raw)) return { id: 'success', label: '处理完成', icon: 'check' }
  if (/fail|error|失败|❌/i.test(raw)) return { id: 'fail', label: '处理失败', icon: 'close' }
  if (/process|进行|处理中|🚀/i.test(raw)) return { id: 'process', label: '处理中', icon: 'clock' }
  return { id: 'unknown', label: raw || '未知状态', icon: 'file' }
}
