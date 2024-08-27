// 主要负责的是与LLM进行对话的接口，LLM输入需要流式输出
import { fetchEventSource } from '@microsoft/fetch-event-source';


export function sendMessage(data: Chat){
    const ctrl = new AbortController();
    fetchEventSource('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      async onopen(response: any) {
        console.log('onopen',response);
      },
      onmessage(ev : any) {
        console.log('fetchEventSource:', ev);
        if(ev.data === '[DONE]'){

        }
      },
      onclose() {
        console.log('onclose');
      },
      onerror(err: any) {
        console.log('onerror', err);
        ctrl.abort();
        throw err;
      }
    });
}



export interface Chat {
    dialogId: string
    userInput: string
}
