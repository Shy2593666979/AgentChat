import type { ChatMessage } from '../type';
export type ChatToolEvent = NonNullable<ChatMessage['eventInfo']>[number];

// 一些搜索工具以字符串返回错误，但结束事件仍为 END；按明确的错误格式展示。
export function chatToolEventState(event: ChatToolEvent) {
    if (event.status === 'END' && /^(?:搜索API请求失败|You\.com Search 请求失败)/.test(event.message.trim())) return 'ERROR';
    return event.status;
}

// 记忆开关与降级提示保留在原始记录中，不占用聊天工具卡片。
export function visibleChatEvents(events: ChatToolEvent[] = []) {
    return events.filter(event => !/长期记忆|长时记忆|long.?term.?memory/i.test(event.event_type));
}

// 同一个工具再次调用时新增卡片，结束事件更新最近一次正在执行的调用。
export function updateChatEvent(events: ChatToolEvent[], title: string, status: string, message: string, toolCallId?: string) {
    const matching = [...events].reverse().find(event => event.event_type === title && event.status === 'START');
    const existing = toolCallId ? events.find(event => event.toolCallId === toolCallId) : matching || (status !== 'START' ? [...events].reverse().find(event => event.event_type === title) : undefined);
    if (existing) {
        existing.status = status;
        if (message) existing.message = message;
    } else events.push({ event_type: title, status, message, show: false, toolCallId });
}
