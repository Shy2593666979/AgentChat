// 主要负责的是与LLM进行对话的接口，LLM输入需要流式输出
import { fetchEventSource } from '@microsoft/fetch-event-source';


export function sendMessage(data: Chat,onmessage:any,onclose:any) {
  const ctrl = new AbortController();


  fetchEventSource('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },


    body: JSON.stringify({
      ...data,
      detail: true,
      stream: true,
    }),
    signal: ctrl.signal,
    openWhenHidden: true,
    async onopen(response: any) {
      // console.log('onopen', response);
    },
    onmessage(msg: any) {
        onmessage(msg)
    },
    onclose() {
      onclose()
    },
    onerror(err: any) {
      // console.log('onerror', err);
      ctrl.abort();
      throw err;
    }
  });
}



export interface Chat {
  dialogId: string
  userInput: string
}



