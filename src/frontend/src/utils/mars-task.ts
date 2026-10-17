export interface MarsProcess { id: string; label: string; icon: string; elapsed?: number; state: 'working' | 'done' | 'error'; }
export interface MarsTask {
  query: string; time: string; answer: string; reasoning: string; error: string; elapsed: number;
  state: 'working' | 'done' | 'error' | 'stopped'; example?: number;
  tools: MarsProcess[]; logs: { message: string; status: string; toolId: string }[];
  outputs: { toolId: string; content: string; resultKey?: string }[];
}
export function createMarsTask(query: string, example?: number): MarsTask {
  return { query, time: new Date().toISOString(), example, answer: '', reasoning: '', error: '', elapsed: 0, state: 'working', tools: [], logs: [], outputs: [] };
}
// 工具状态、分析过程和结果分别保存，复制与下载只读取结果。
export function consumeMarsEvent(task: MarsTask, event: { type: string; data?: any; tool_id?: string; source?: string; result_key?: string }) {
  const data = event.data, text = typeof data === 'string' ? data : typeof data?.chunk === 'string' ? data.chunk : '';
  if (event.type === 'reasoning_chunk') task.reasoning += text;
  else if (event.type === 'result_start' && event.result_key) {
    // 同一份搜索报告重新生成时替换旧版本，不把两份完整攻略拼接。
    let block = task.outputs.find(item => item.resultKey === event.result_key);
    if (!block) { block = { toolId: event.tool_id || 'direct', content: '', resultKey: event.result_key }; task.outputs.push(block); }
    block.toolId = event.tool_id || 'direct'; block.content = '';
    task.answer = task.outputs.filter(item => item.content).map(item => item.content).join('\n\n---\n\n');
  }
  else if (['response_chunk', 'answer', 'answer_chunk', 'tool_chunk'].includes(event.type) && text) {
    const identity = event.tool_id || (event.source === 'reasoning' ? 'reasoning' : 'direct');
    let block = event.result_key ? task.outputs.find(item => item.resultKey === event.result_key) : task.outputs.find(item => item.toolId === identity);
    // 后一次生成已经开始时，忽略旧调用迟到的片段。
    if (block && event.result_key && block.toolId !== identity) return;
    if (!block) { block = { toolId: identity, content: '', resultKey: event.result_key }; task.outputs.push(block); }
    block.content += text;
    task.answer = task.outputs.filter(item => item.content).map(item => item.content).join('\n\n---\n\n');
  }
  else if (event.type === 'progress_chunk' && data?.message) task.logs.push({ message: data.message, status: data.status, toolId: event.tool_id || '' });
  else if (['tool_start', 'tool_end', 'tool_error'].includes(event.type) && data?.id) {
    if (event.type === 'tool_start' && !task.tools.length) {
      // 工具接手后，用工具实际结果替换推理模型的临时回答。
      task.outputs = task.outputs.filter(item => item.toolId !== 'reasoning');
      task.answer = task.outputs.map(item => item.content).join('\n\n---\n\n');
    }
    let tool = task.tools.find(item => item.id === data.id);
    if (!tool) { tool = { id: data.id, label: data.label || data.name || '执行工具', icon: data.icon || 'tool', state: 'working' }; task.tools.push(tool); }
    if (typeof data.elapsed === 'number') tool.elapsed = data.elapsed;
    tool.state = event.type === 'tool_end' ? 'done' : event.type === 'tool_error' ? 'error' : 'working';
  } else if (event.type === 'error') { task.state = 'error'; task.error = text || data?.message || '任务执行失败，请重试'; }
}
