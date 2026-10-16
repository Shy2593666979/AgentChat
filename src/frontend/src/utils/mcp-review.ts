export function maskMcpParameters(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(maskMcpParameters);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,/key|secret|password|token|authorization|credential|cookie/i.test(key)?'••••••':maskMcpParameters(item)]));
    if(typeof value==='string'){
        const json=value.replace(/^VERIFY_SUCCESS:\s*/,'');
        if(/^[{[]/.test(json.trim())){try{return JSON.stringify(maskMcpParameters(JSON.parse(json)),null,2);}catch{/* 保留非 JSON 的工具说明。 */}}
        return value.replace(/(https?:\/\/)[^\s/@]+:[^\s/@]+@/g,'$1••••••@').replace(/([?&](?:api[_-]?key|token|secret|password)=)[^&#\s]+/gi,'$1••••••');
    }
    return value;
}
export function mcpReviewServices(data: any) {
    return (data.action_requests||[]).flatMap((action:any)=>{
        try{const raw=action.arguments?.mcp_json_str||'';const config=typeof raw==='string'?JSON.parse(raw.replace(/^VERIFY_SUCCESS:\s*/,'')):raw;
            return Object.entries(config?.mcpServers||{}).map(([name,server])=>({name,...maskMcpParameters(server) as Record<string,unknown>}));
        }catch{return [];}
    });
}
export function latestMcpPending(content: Array<{type:string;data:any}> = []) {
    const latest=[...content].reverse().find(item=>item.type==='interrupt');
    return latest?.data?.status===false?latest.data:undefined;
}
