// 展示名称仅用于界面；模型请求仍使用 model，选择值仍使用 llm_id。
export function modelDisplayName(model?: { show_model?: string; model?: string }) {
  return model?.show_model?.trim() || model?.model || '模型未配置';
}
