// 主要负责的是与LLM进行对话的接口，LLM输入需要流式输出
import { fetchEventSource } from '@microsoft/fetch-event-source';

export interface Chat {
  dialogId: string
  userInput: string
  fileUrl?: string
}

export interface UploadResponse {
  code: number
  message: string
  data: string
}

export function sendMessage(data: Chat, onmessage: any, onclose: any) {
  const ctrl = new AbortController();

  fetchEventSource('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify({
      ...(data.fileUrl
        ? {
            dialog_id: data.dialogId,
            user_input: data.userInput,
            file_url: data.fileUrl,
          }
        : {
            dialog_id: data.dialogId,
            user_input: data.userInput,
          }),
    }),
    signal: ctrl.signal,
    openWhenHidden: true,
    async onopen(response: any) {
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    },
    onmessage(msg: any) {
      try {
        onmessage(msg);
      } catch (error) {
        console.error('处理消息时出错:', error);
      }
    },
    onclose() {
      onclose();
    },
    onerror(err: any) {
      console.error('聊天连接错误:', err);
      ctrl.abort();
      throw err;
    }
  });

  return ctrl;
}

// 文件上传功能
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/v1/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: formData
  });

  if (!response.ok) {
    throw new Error(`上传失败: ${response.statusText}`);
  }

  return await response.json();
}

// 知识库检索功能
export async function retrieveKnowledge(query: string, knowledgeIds: string | string[]) {
  const response = await fetch('/api/v1/knowledge/retrieval', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify({
      query,
      knowledge_id: knowledgeIds
    })
  });

  if (!response.ok) {
    throw new Error(`检索失败: ${response.statusText}`);
  }

  return await response.json();
}

// Mars示例功能
export function sendMarsExample(exampleId: number, onmessage: any, onclose: any) {
  const ctrl = new AbortController();

  fetchEventSource('/api/v1/mars/example', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify({
      example_id: exampleId
    }),
    signal: ctrl.signal,
    openWhenHidden: true,
    async onopen(response: any) {
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    },
    onmessage(msg: any) {
      try {
        onmessage(msg);
      } catch (error) {
        console.error('处理消息时出错:', error);
      }
    },
    onclose() {
      onclose();
    },
    onerror(err: any) {
      console.error('Mars示例连接错误:', err);
      ctrl.abort();
      throw err;
    }
  });

  return ctrl;
}



