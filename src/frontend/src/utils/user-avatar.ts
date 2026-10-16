import { safeResourceUrl } from './data-pages';

// 旧系统随机头像与占位图片改用首字母；保留用户自行上传的图片。
export function userAvatarUrl(value?: string) {
  const url = safeResourceUrl(value);
  if (!url) return '';
  const path = new URL(url).pathname;
  return /\/icons\/user\//i.test(path) || /\/(?:default-avatar\.[^/]+|(?:src\/)?assets\/user\.svg)$/i.test(path) ? '' : url;
}
export function userInitial(username?: string) {
  return Array.from((username || '').trim())[0]?.toLocaleUpperCase() || 'U';
}
