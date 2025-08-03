import { fetchEventSource } from '@microsoft/fetch-event-source';

// 发送Mars聊天消息
export function sendMarsChat(userInput: string, abortController: AbortController, 
                            onmessage: (msg: any) => void, 
                            onclose: () => void, 
                            onerror: (err: any) => void) {
  fetchEventSource('/api/v1/mars/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify({
      user_input: userInput,
    }),
    signal: abortController.signal,
    openWhenHidden: true,
    async onopen(response) {
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    },
    onmessage,
    onclose,
    onerror
  });
}

// 发送Mars示例请求
export function sendMarsExample(exampleId: number, abortController: AbortController, 
                               onmessage: (msg: any) => void, 
                               onclose: () => void, 
                               onerror: (err: any) => void) {
  fetchEventSource('/api/v1/mars/example', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
    },
    body: JSON.stringify({
      example_id: exampleId,
    }),
    signal: abortController.signal,
    openWhenHidden: true,
    async onopen(response) {
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    },
    onmessage,
    onclose,
    onerror
  });
} 