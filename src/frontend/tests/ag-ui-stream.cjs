// 使用真实 TypeScript 模块验证协议消费，不需要浏览器或模型服务。
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');

function load(relative) {
    const filename = path.resolve(__dirname, '../src', relative);
    const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
        compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }
    }).outputText;
    const mod = new Module(filename, module);
    mod.filename = filename;
    mod.paths = Module._nodeModulePaths(path.dirname(filename));
    mod._compile(compiled, filename);
    return mod.exports;
}
const { AgUiStreamReader } = load('utils/ag-ui-stream.ts');
const { updateChatEvent } = load('utils/chat-tool-events.ts');
const start = { type: 'RUN_STARTED', threadId: 'dialog', runId: 'run' };
const end = { type: 'RUN_FINISHED', threadId: 'dialog', runId: 'run', outcome: { type: 'success' } };

test('并行同名工具按调用 ID 更新各自卡片', () => {
    const reader = new AgUiStreamReader('/api/v1/completion');
    const cards = [];
    reader.consume(start);
    for (const id of ['a', 'b']) {
        for (const event of reader.consume({ type: 'TOOL_CALL_START', toolCallId: id, toolCallName: 'search', metadata: { title: '搜索' } })) {
            updateChatEvent(cards, event.data.title, event.data.status, event.data.message, event.data.tool_call_id);
        }
    }
    for (const id of ['b', 'a']) {
        const [event] = reader.consume({ type: 'TOOL_CALL_RESULT', toolCallId: id, messageId: `result-${id}`, content: id, metadata: { status: 'END' } });
        updateChatEvent(cards, event.data.title, event.data.status, event.data.message, event.data.tool_call_id);
    }
    assert.deepEqual(cards.map(card => [card.toolCallId, card.message]), [['a', 'a'], ['b', 'b']]);
});

test('意外断线和异常事件不会被当成成功', () => {
    const reader = new AgUiStreamReader('/api/v1/completion');
    reader.consume(start);
    assert.throws(() => reader.assertFinished(), /中断/);
    assert.throws(() => reader.consume({ type: 'RUN_ERROR', message: '模型不可用' }), /模型不可用/);
    assert.equal(reader.finished, true);
});

test('拒绝没有开始事件的分片和不完整的消息', () => {
    const reader = new AgUiStreamReader('/api/v1/completion');
    assert.throws(() => reader.consume({ type: 'TEXT_MESSAGE_CONTENT', messageId: 'm', delta: '内容' }), /开始/);
    reader.consume(start);
    reader.consume({ type: 'TEXT_MESSAGE_START', messageId: 'm', role: 'assistant' });
    assert.throws(() => reader.consume(end), /不一致/);
    assert.throws(() => reader.consume({ type: 'TEXT_MESSAGE_CONTENT', messageId: 'm', delta: 42 }), /结构/);
});

test('MCP 中断保留审批内容和标识', () => {
    const reader = new AgUiStreamReader('/api/v1/mcp/register/completion');
    reader.consume(start);
    const [event] = reader.consume({ ...end, outcome: { type: 'interrupt', interrupts: [{ id: 'approval', reason: 'confirmation', metadata: { allowed_decisions: ['approve', 'reject'] } }] } });
    assert.equal(event.type, 'interrupt');
    assert.equal(event.event.interrupt_id, 'approval');
    assert.equal(event.event.status, false);
    reader.assertFinished();
});

test('消费 Python SDK 实际编码的四类事件流', { skip: !process.env.AG_UI_FIXTURE }, () => {
    const corpus = JSON.parse(fs.readFileSync(process.env.AG_UI_FIXTURE, 'utf8'));
    for (const { url, events, expected } of corpus) {
        const reader = new AgUiStreamReader(url);
        const output = events.flatMap(event => reader.consume(event));
        reader.assertFinished();
        for (const type of expected) assert.ok(output.some(event => event.type === type), `${url}: ${type}`);
    }
});
