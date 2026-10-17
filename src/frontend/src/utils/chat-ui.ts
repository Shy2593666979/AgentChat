import { fetchEventSource } from '@microsoft/fetch-event-source';
import { formatDataDate, safeResourceUrl } from './data-pages';
import type { ChatMessage } from '../type';
import { updateChatEvent } from './chat-tool-events';
import { AgUiStreamReader } from './ag-ui-stream';
export function historyGroup(value?: string) {
    const date = formatDataDate(value, false);
    if (date === '—')
        return '更早';
    const today = formatDataDate(new Date().toISOString(), false);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    if (date === today)
        return '今天';
    if (date === formatDataDate(yesterday.toISOString(), false))
        return '昨天';
    const week = new Date();
    week.setDate(week.getDate() - 7);
    return date >= formatDataDate(week.toISOString(), false) ? '过去 7 天' : '更早';
}
export function historyTime(value?: string) {
    const date = formatDataDate(value);
    if (date === '—')
        return date;
    const group = historyGroup(value);
    return group === '今天' ? date.slice(-5) : group === '昨天' ? '昨天 ' + date.slice(-5) : date.slice(5, 10);
}
export function isSendKey(event: KeyboardEvent) {
    return event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey && !event.isComposing && event.keyCode !== 229;
}
export function parseStringArray(value: unknown) {
    if (typeof value !== 'string')
        return [];
    try {
        const result = JSON.parse(value);
        return Array.isArray(result) ? result.filter((item): item is string => typeof item === 'string') : [];
    }
    catch {
        return [];
    }
}
export function normalizeHistory(messages: any[]): ChatMessage[] {
    const rows: ChatMessage[] = [];
    for (const message of messages) {
        if (message.role === 'user')
            rows.push({ personMessage: { content: String(message.content || ''), attachments: (Array.isArray(message.events) ? message.events : []).filter((event: any) => event.type === 'attachment' && safeResourceUrl(event.data?.url)).map((event: any) => ({ url: safeResourceUrl(event.data.url), name: String(event.data.name || '附件'), size: typeof event.data.size === 'number' ? event.data.size : undefined, mime: event.data.mime })) }, aiMessage: { content: '' }, eventInfo: [] });
        else if (message.role === 'assistant') {
            let row = rows[rows.length - 1];
            if (!row || row.aiMessage.content || row.eventInfo?.length) {
                row = { personMessage: { content: '' }, aiMessage: { content: '' }, eventInfo: [] };
                rows.push(row);
            }
            row.aiMessage.content = String(message.content || '');
            const events: NonNullable<ChatMessage['eventInfo']> = [];
            for (const event of Array.isArray(message.events) ? message.events : []) {
                if (event.type === 'agent') {
                    row.aiMessage.agent = { id: String(event.data?.agent_id || ''), name: String(event.data?.name || '智能体'), logo_url: String(event.data?.logo_url || '') };
                    continue;
                }
                if (event.type === 'heartbeat')
                    continue;
                const title = event.data?.title || event.data?.event_type || event.type || '事件';
                updateChatEvent(events, title, event.data?.status || 'UNKNOWN', event.data?.message || '', event.data?.tool_call_id);
            }
            row.eventInfo = events;
        }
    }
    return rows;
}
export async function postEventStream(path: string, data: unknown, onEvent: (event: any) => void, signal: AbortSignal) {
    const base = import.meta.env.VITE_API_BASE_URL || '';
    const reader = new AgUiStreamReader(path);
    await fetchEventSource(base + path, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-AgentChat-Protocol': 'ag-ui/1.0', Authorization: 'Bearer ' + (localStorage.getItem('token') || '') },
        body: JSON.stringify(data), signal, openWhenHidden: true,
        async onopen(response) {
            if (!response.ok)
                throw new Error(`请求失败（HTTP ${response.status}）`);
            if (!response.headers.get('content-type')?.includes('text/event-stream'))
                throw new Error('服务未返回有效的流式响应');
        },
        onmessage(event) {
            const text = event.data.trim();
            if (!text || ['DONE', '[DONE]'].includes(text))
                return;
            const value = JSON.parse(text);
            if (/^[A-Z_]+$/.test(value.type || '')) {
                for (const normalized of reader.consume(value)) onEvent(normalized);
                return;
            }
            if (reader.started) throw new Error('同一响应中混入了不同版本的流式事件');
            if (value.type === 'error' || value.event === 'error')
                throw new Error(value.data?.message || value.message || '任务处理失败');
            onEvent(value);
        },
        onclose() { if (reader.started) reader.assertFinished(); },
        onerror(error) { throw error; }
    });
}
export async function copyChatText(value: string) {
    await navigator.clipboard.writeText(value);
}
export function fitComposer(element?: HTMLTextAreaElement) {
    if (!element) return;
    element.style.height = 'auto';
    element.style.height = Math.min(160, Math.max(40, element.scrollHeight)) + 'px';
}
export function downloadMarkdown(value: string, name: string) {
    const url = URL.createObjectURL(new Blob([value], { type: 'text/markdown;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = (name.replace(/[\\/:*?"<>|]/g, '_').slice(0, 80) || '任务报告') + '.md';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
