export const modelProviders = ['OpenAI', 'Anthropic', 'Google', '千问', '智谱 AI', '豆包', 'MiniMax', 'DeepSeek', '腾讯混元', '月之暗面', '小米 MiMo'];

// 仅统一界面名称，保留现有模型标识、密钥和接口地址。
export function modelProviderDisplayName(provider = '') {
    const name = provider.trim();
    if (/^(阿里云|阿里巴巴|通义千问|通义|qwen|aliyun|alibaba(?: cloud)?)$/i.test(name)) return '千问';
    if (/^(火山引擎|火山|volcengine|volces)$/i.test(name)) return '豆包';
    if (/^(腾讯云|tencentcloud|tencent cloud)$/i.test(name)) return '腾讯混元';
    if (/^(小米|小米\s*mimo|xiaomi(?:\s*mimo)?|mimo)$/i.test(name)) return '小米 MiMo';
    return name;
}

function brandFromName(value: string) {
    const name = value.trim().toLowerCase();
    if (/xiaomi|小米|\bmimo(?:[-_\s.]|$)/.test(name)) return 'xiaomi';
    if (/qwen|千问|通义/.test(name)) return 'qwen';
    if (/deepseek|深度求索/.test(name)) return 'deepseek';
    if (/doubao|豆包/.test(name)) return 'doubao';
    if (/minimax|mini-max|稀宇|海螺|\babab\d/.test(name)) return 'minimax';
    if (/chatglm|\bglm(?:[-_\s.]|\d|$)/.test(name)) return 'chatglm';
    if (/智谱|zhipu|z\.ai|^zai$|bigmodel/.test(name)) return 'zhipu';
    if (/hunyuan|混元/.test(name)) return 'hunyuan';
    if (/tencentcloud|腾讯云/.test(name)) return 'tencentcloud';
    if (/tencent|腾讯/.test(name)) return 'tencent';
    if (/kimi/.test(name)) return 'kimi';
    if (/moonshot|月之暗面/.test(name)) return 'moonshot';
    if (/volcengine|volces|火山|字节|bytedance/.test(name)) return 'volcengine';
    return '';
}

function brandFromUrl(value?: string) {
    if (!value) return '';
    let host: string;
    try { host = new URL(value).hostname.toLowerCase(); } catch { return ''; }
    const is = (domain: string) => host === domain || host.endsWith('.' + domain);
    if (is('volces.com') || is('volcengine.com')) return 'doubao';
    if (is('xiaomimimo.com') || is('mimo.xiaomi.com')) return 'xiaomi';
    if (is('dashscope.aliyuncs.com')) return 'qwen';
    if (is('bigmodel.cn') || is('z.ai')) return 'zhipu';
    if (is('minimax.chat') || is('minimaxi.com') || is('minimax.io')) return 'minimax';
    if (is('deepseek.com')) return 'deepseek';
    if (is('hunyuan.cloud.tencent.com') || is('hunyuan.tencent.com')) return 'hunyuan';
    if (is('tencentcloudapi.com') || is('cloud.tencent.com')) return 'hunyuan';
    if (is('moonshot.cn') || is('moonshot.ai')) return 'moonshot';
    return '';
}

export function modelProviderBrand(provider: string, model?: string, baseUrl?: string, modelMark = false) {
    // 模型列优先识别模型品牌；未知编号（例如 ep-...）回退到真实提供方。
    return (modelMark ? brandFromName(model || '') : '') || brandFromName(modelProviderDisplayName(provider || '')) || brandFromUrl(baseUrl);
}
