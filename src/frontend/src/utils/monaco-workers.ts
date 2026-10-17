import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import JsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'

// JSON configuration and MCP editors need their own language worker in Vite.
// Keep worker URLs local so development and production use the same setup.
const workerHost = self as unknown as {
  MonacoEnvironment: { getWorker: (moduleId: string, label: string) => Worker }
}
workerHost.MonacoEnvironment = {
  getWorker(_moduleId, label) {
    return label === 'json' ? new JsonWorker() : new EditorWorker()
  }
}
