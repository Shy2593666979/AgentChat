const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync(require('node:path').join(__dirname, '../src/utils/mars-task.ts'), 'utf8');
const sandbox = { exports: {} };
vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, sandbox);
const { createMarsTask, consumeMarsEvent } = sandbox.exports;
function start(task, id) { consumeMarsEvent(task, { type: 'result_start', tool_id: id, result_key: 'deep_search' }); }
function write(task, id, text) { consumeMarsEvent(task, { type: 'response_chunk', tool_id: id, result_key: 'deep_search', data: text }); }

test('两次搜索只保留一份完整攻略，旧调用的迟到片段不混入新报告', () => {
  const task = createMarsTask('泰山攻略');
  start(task, 'search-1'); write(task, 'search-1', '# 泰山游玩攻略\n第一份完整正文');
  start(task, 'search-2'); write(task, 'search-2', '# 泰山旅游攻略\n');
  write(task, 'search-1', '旧版本的迟到内容'); write(task, 'search-2', '第二份完整正文');
  assert.equal(task.answer, '# 泰山旅游攻略\n第二份完整正文');
  assert.equal(task.outputs.length, 1);
});

test('同一次工具调用重新生成时也替换旧报告', () => {
  const task = createMarsTask('泰山攻略');
  start(task, 'search'); write(task, 'search', '旧报告');
  start(task, 'search'); write(task, 'search', '新报告');
  assert.equal(task.answer, '新报告');
});

test('替换搜索报告不删除知识库等其他工具的结果', () => {
  const task = createMarsTask('先检索知识，再搜索');
  consumeMarsEvent(task, { type: 'response_chunk', tool_id: 'knowledge', data: '知识库摘要' });
  start(task, 'search-1'); write(task, 'search-1', '旧攻略');
  start(task, 'search-2'); write(task, 'search-2', '最终攻略');
  assert.equal(task.answer, '知识库摘要\n\n---\n\n最终攻略');
});
