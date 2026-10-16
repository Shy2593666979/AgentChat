import { EventSchema } from '@ag-ui/core/schemas';

// AG-UI 事件只在此处转换为现有页面的展示事件，页面不再解析线上协议差异。
export type AgUiEvent = Record<string, any> & { type: string };
type Scene = 'conversation' | 'mars' | 'workspace' | 'mcp';

export class AgUiStreamReader {
    started = false;
    finished = false;
    private messages = new Map<string, Record<string, any>>();
    private tools = new Map<string, Record<string, any>>();
    private scene: Scene;
    private runId = '';
    private threadId = '';

    constructor(path: string) {
        this.scene = path.includes('/mcp/register/') ? 'mcp' : path.includes('/mars/') ? 'mars' : path.includes('/workspace/') ? 'workspace' : 'conversation';
    }

    consume(event: AgUiEvent): AgUiEvent[] {
        const parsed = EventSchema.safeParse(event);
        if (!parsed.success) throw new Error('无效的 AG-UI 事件结构');
        event = parsed.data;
        if (this.finished) throw new Error('任务结束后仍收到事件');
        if (event.type === 'RUN_STARTED') {
            if (this.started || !event.runId || !event.threadId) throw new Error('无效的运行开始事件');
            this.started = true;
            this.runId = event.runId;
            this.threadId = event.threadId;
            return [];
        }
        if (!this.started) throw new Error('缺少运行开始事件');
        if (event.type === 'RUN_ERROR') {
            this.finished = true;
            throw new Error(event.message || '执行失败，请重试');
        }
        if (event.type === 'RUN_FINISHED') {
            if (event.runId !== this.runId || event.threadId !== this.threadId || this.messages.size) throw new Error('运行结束事件与当前消息状态不一致');
            this.finished = true;
            if (event.outcome?.type === 'interrupt') {
                if (this.scene !== 'mcp') throw new Error('当前页面不支持人工确认');
                return (event.outcome.interrupts || []).map((item: any) => ({ type: 'interrupt', content: '', event: { ...item.metadata, interrupt_id: item.id, status: false } }));
            }
            return [];
        }
        if (event.type === 'TEXT_MESSAGE_START') {
            if (!event.messageId || this.messages.has(event.messageId)) throw new Error('无效的消息开始事件');
            this.messages.set(event.messageId, event.metadata || {});
            return [];
        }
        if (event.type === 'TEXT_MESSAGE_CONTENT') {
            const metadata = this.messages.get(event.messageId);
            if (!metadata || typeof event.delta !== 'string') throw new Error('无效的消息分片');
            if (this.scene === 'mcp') return [{ type: 'text', content: event.delta }];
            if (this.scene === 'workspace') return [{ type: 'workspace_text', event: 'task_result', data: { chunk: event.delta, message: event.delta } }];
            if (this.scene === 'mars') return [{ type: 'response_chunk', data: event.delta, ...metadata, ...event.metadata }];
            return [{ type: 'response_chunk', data: { chunk: event.delta } }];
        }
        if (event.type === 'TEXT_MESSAGE_END') {
            if (!this.messages.delete(event.messageId)) throw new Error('无效的消息结束事件');
            return [];
        }
        if (event.type === 'TOOL_CALL_START') {
            if (!event.toolCallId || !event.toolCallName || this.tools.has(event.toolCallId)) throw new Error('无效的工具调用');
            const tool = { ...event.metadata, id: event.toolCallId, name: event.toolCallName };
            this.tools.set(event.toolCallId, tool);
            return [this.toolEvent(tool, 'START', '')];
        }
        if (event.type === 'TOOL_CALL_ARGS' || event.type === 'TOOL_CALL_END') {
            if (!this.tools.has(event.toolCallId)) throw new Error('工具调用标识不存在');
            return [];
        }
        if (event.type === 'TOOL_CALL_RESULT') {
            const tool = this.tools.get(event.toolCallId);
            if (!tool) throw new Error('工具结果缺少对应调用');
            return [this.toolEvent({ ...tool, ...event.metadata }, event.metadata?.status || 'END', typeof event.content === 'string' ? event.content : JSON.stringify(event.content))];
        }
        if (event.type === 'REASONING_MESSAGE_CONTENT') return [{ type: 'reasoning_chunk', data: event.delta }];
        if (event.type === 'STEP_STARTED' && this.scene === 'workspace') return [{ type: 'workspace_step', event: 'step_start', data: { title: event.stepName } }];
        if (['REASONING_START', 'REASONING_END', 'REASONING_MESSAGE_START', 'REASONING_MESSAGE_END', 'STEP_FINISHED'].includes(event.type)) return [];
        if (event.type === 'STATE_SNAPSHOT' && this.scene === 'workspace') return [{ type: 'workspace_graph', event: 'generate_tasks', data: event.snapshot }];
        if (event.type === 'CUSTOM') return this.custom(event);
        throw new Error(`不支持的 AG-UI 事件：${event.type}`);
    }

    private toolEvent(tool: Record<string, any>, status: string, content: string): AgUiEvent {
        if (this.scene === 'mars') return { type: status === 'START' ? 'tool_start' : status === 'ERROR' ? 'tool_error' : 'tool_end', data: tool };
        if (this.scene === 'mcp') return { type: 'event', event: { tool_call_id: tool.id, title: tool.title || tool.name, status, is_error: status === 'ERROR', content } };
        return { type: 'event', data: { tool_call_id: tool.id, title: tool.title || tool.name, status, message: content } };
    }

    private custom(event: AgUiEvent): AgUiEvent[] {
        const data = event.value;
        if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('自定义事件数据必须是对象');
        switch (event.name) {
            case 'agentchat.agent': return [{ type: 'agent', data }];
            case 'agentchat.knowledge': return [{ type: 'knowledge', data }];
            case 'agentchat.notice': return [{ type: 'event', data }];
            case 'agentchat.mcp.progress': return [{ type: 'event', event: data }];
            case 'agentchat.workspace.step_result': return [{ type: 'workspace_step', event: 'step_result', data }];
            case 'agentchat.mars.progress': return [{ type: 'progress_chunk', tool_id: data.tool_id, data }];
            case 'agentchat.mars.result_start': return [{ type: 'result_start', ...data }];
            default: throw new Error(`不支持的自定义事件：${event.name}`);
        }
    }

    assertFinished() {
        if (!this.finished) throw new Error('流式连接意外中断，已保留收到的内容，请重试');
    }
}
