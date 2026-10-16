<script setup lang="ts">
import { computed, ref } from 'vue';
import UiIcon from './UiIcon.vue';
import { historyGroup, historyTime } from '../utils/chat-ui';
import { useScrollingScrollbar } from '../utils/scrolling-scrollbar';
const { scrolling, showScrollbar } = useScrollingScrollbar();
const props = withDefaults(defineProps<{
    title: string;
    variant?: 'default' | 'conversation';
    records: Array<{
        id: string;
        title: string;
        preview?: string;
        time?: string;
    }>;
    selected?: string;
    loading?: boolean;
    error?: string;
    open?: boolean;
    creating?: boolean;
    deleting?: boolean;
    allowDelete?: boolean;
    createLabel?: string;
}>(), { variant: 'default', loading: false, error: '', open: false, creating: false, deleting: false, allowDelete: false, createLabel: '新建任务' });
const emit = defineEmits<{
    select: [
        id: string
    ];
    create: [
    ];
    remove: [
        id: string
    ];
    retry: [
    ];
    'update:open': [
        value: boolean
    ];
}>();
const search = ref('');
const visible = computed(() => props.records.filter(record => [record.title, record.preview].join(' ').toLowerCase().includes(search.value.trim().toLowerCase())));
const groups = computed(() => props.variant === 'conversation' ? ['今天', '昨天', '过去 7 天', '更早'].map(label => ({ label, records: visible.value.filter(record => historyGroup(record.time) === label) })).filter(group => group.records.length) : [{ label: '', records: visible.value }]);
</script>
<template><div v-if="open" class="session-rail-scrim" @click="emit('update:open',false)"/><aside class="session-rail" :class="{open, 'conversation-rail':variant==='conversation'}"><header><h2 v-if="variant !== 'conversation'">{{title}}</h2><button class="rail-close" aria-label="关闭记录" @click="emit('update:open',false)"><UiIcon name="close"/></button></header><button class="rail-new" :disabled="creating" @click="emit('create')"><UiIcon :name="creating?'clock':'plus'"/>{{creating?'创建中…':createLabel}}</button><label class="rail-search"><UiIcon name="search"/><input v-model="search" type="search" :placeholder="variant === 'conversation' ? '搜索会话…' : '搜索记录…'" :aria-label="variant === 'conversation' ? '搜索会话' : '搜索记录'"></label><p v-if="error" class="rail-error" role="alert">{{error}}<button @click="emit('retry')">重试</button></p><div class="rail-list scrollbar-on-scroll" :class="{ 'is-scrolling': scrolling }" v-loading="loading" @scroll.passive="showScrollbar"><section v-for="group in groups" :key="group.label"><h3 v-if="group.label" class="rail-group-title">{{group.label}}</h3><article v-for="record in group.records" :key="record.id" :class="{selected:selected===record.id}"><button class="rail-record" :title="record.title" @click="emit('select',record.id);emit('update:open',false)"><span class="rail-record-icon"><UiIcon :name="variant === 'conversation' ? 'chat' : 'file'"/></span><span class="rail-record-copy"><strong>{{record.title}}</strong><small v-if="variant !== 'conversation' && record.preview && record.preview !== record.title">{{record.preview}}</small><time>{{historyTime(record.time)}}</time></span></button><el-dropdown v-if="allowDelete" trigger="click"><button class="rail-more" :aria-label="`${record.title}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item :disabled="deleting" @click="emit('remove',record.id)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除记录</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></article></section><p v-if="!loading&&!visible.length" class="rail-empty">{{error?'记录暂时无法读取':search?'没有匹配的记录':variant==='conversation'?'暂无会话记录':'暂无任务记录'}}</p></div><footer v-if="$slots.footer" class="rail-footer"><slot name="footer"/></footer></aside></template>
<style scoped>.session-rail{display:flex;flex-direction:column;width:275px;flex:none;min-height:0;overflow:hidden;background:#ffffffdd;border:1px solid #e2ecfb;border-radius:16px;padding:16px 12px 12px;font-family:'AgentChat Inter','AgentChat Sans SC',sans-serif}.session-rail>header{display:flex;align-items:center;justify-content:space-between;margin:0 4px 15px}.session-rail h2{font-size:18px;font-weight:650;line-height:1.6;color:#14284f;margin:0}.rail-new{display:flex;align-items:center;justify-content:center;gap:12px;background:linear-gradient(125deg,#1980ff,#1260ff);color:white;min-height:47px;border:0;border-radius:11px;font:inherit;font-size:15px;cursor:pointer;margin-bottom:14px}.rail-new .p-icon{width:22px;height:22px}.rail-search{display:flex;align-items:center;gap:9px;min-height:38px;border:1px solid #dee9fc;background:#fbfdff;border-radius:9px;padding:0 11px;margin-bottom:14px;color:#8da2bf}.rail-search .p-icon{width:17px;height:17px}.rail-search input{min-width:0;flex:1;border:0;outline:0;background:transparent;font:inherit;font-size:12px;color:#415d85}.rail-search input::placeholder{color:#9fadc3}.rail-list{flex:1;min-height:0;overflow:auto;scrollbar-width:thin}.rail-list article{display:flex;align-items:center;margin:0 0 12px;border-radius:12px;padding:12px 9px;min-width:0}.rail-list article.selected{background:linear-gradient(110deg,#e4f1ff,#eaf4ff)}.rail-record{display:flex;align-items:flex-start;gap:15px;border:0;background:transparent;padding:0;flex:1;min-width:0;text-align:left;cursor:pointer;color:#263e68;font:inherit}.rail-record-icon{display:grid;place-items:center;flex:none;width:31px;height:36px;color:#5e7ead;margin-top:4px}.rail-record-icon .p-icon{width:27px;height:27px}.selected .rail-record-icon{color:#096aff}.rail-record-copy{flex:1;min-width:0}.rail-record-copy strong{display:block;font-size:14px;font-weight:600;color:#122c58;line-height:1.6;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.selected .rail-record-copy strong{color:#126aff}.rail-record-copy small{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:#8ba0c0;font-size:12px;line-height:1.7;margin-top:3px}.rail-record-copy time{display:block;color:#94a6c2;font-size:12px;line-height:1.7;margin-top:4px}.rail-more{display:grid;place-items:center;background:transparent;border:0;color:#8ca4c6;width:21px;height:27px;padding:0;opacity:0;cursor:pointer}.rail-more .p-icon{width:16px;height:16px}.rail-list article:hover .rail-more,.rail-list article:focus-within .rail-more{opacity:1}.rail-empty{padding:25px 10px;color:#99aac4;text-align:center;font-size:12px;line-height:1.8}.rail-error{font-size:12px;line-height:1.7;border:1px solid #f1d8df;border-radius:8px;padding:10px;color:#bd5970;background:#fff5f7;margin:0 0 10px}.rail-error button{font:inherit;border:0;background:transparent;color:#1767ff;margin-left:6px;cursor:pointer}.rail-close,.session-rail-scrim{display:none}.session-rail button:focus-visible{outline:3px solid #9ebeff;outline-offset:3px}.session-rail button:disabled{opacity:.5;cursor:not-allowed}@media(max-width:1400px){.session-rail{width:240px}.rail-record{gap:11px}.rail-record-copy strong{font-size:13px}.rail-list article{padding-inline:7px}}@media(max-width:1050px){.session-rail{display:none;position:absolute;left:12px;top:74px;bottom:12px;z-index:51;width:275px;max-width:calc(100% - 24px);background:#fff;box-shadow:0 12px 45px #21447928}.session-rail.open{display:flex}.session-rail-scrim{display:block;position:absolute;inset:0;background:#17365e40;z-index:50}.rail-close{display:grid;place-items:center;width:26px;height:26px;border:0;background:#f1f6ff;border-radius:50%;color:#7b95b8;cursor:pointer}.rail-close .p-icon{width:16px;height:16px}}@media(max-width:700px){.session-rail{left:8px;top:65px;bottom:8px}.rail-more{opacity:1}}</style>

<style scoped>
.conversation-rail{padding:18px 16px 12px}.conversation-rail>header{display:none}.conversation-rail .rail-new{height:50px;font-size:18px;border-radius:12px;background:linear-gradient(125deg,#358bff,#2360ff);gap:12px;margin-bottom:15px}.conversation-rail .rail-new .p-icon{width:23px;height:23px}.conversation-rail .rail-search{height:42px;flex:none;border-radius:11px;padding:0 13px;gap:10px;background:#f9fcff;margin-bottom:15px}.conversation-rail .rail-search input{font-size:15px}.conversation-rail .rail-search .p-icon{width:18px;height:18px}.rail-group-title{font-size:14px;font-weight:400;color:#8798b4;margin:8px 2px 9px}.conversation-rail .rail-list section{margin-bottom:20px}.conversation-rail .rail-list article{min-height:72px;border-radius:11px;margin-bottom:7px;padding:7px 12px}.conversation-rail .rail-list article.selected{background:linear-gradient(110deg,#e5f0ff,#eef5ff)}.conversation-rail .rail-record{gap:11px;align-items:flex-start;padding:4px 2px}.conversation-rail .rail-record-icon{width:36px;height:36px;border-radius:11px;background:#edf5ff;margin-top:4px;color:#6b8cbd}.conversation-rail .rail-record-icon .p-icon{width:26px;height:26px}.conversation-rail .selected .rail-record-icon{background:#dceaff;color:#1767ff}.conversation-rail .rail-record-copy strong{font-size:14px;line-height:1.5;font-weight:550;color:#264269}.conversation-rail .rail-record-copy time{margin-top:7px;color:#95a5c0;font-size:12px}.conversation-rail .rail-more{opacity:1;width:25px;height:27px}.rail-footer{display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-top:1px solid #e5edf8;padding-top:12px;margin-top:8px;flex:none}
@media(max-width:1050px){.conversation-rail>header{display:flex;justify-content:flex-end;margin-bottom:8px}}@media(max-width:700px){.conversation-rail{padding:14px 12px}}
</style>

<style scoped src="../styles/scrolling-scrollbar.css"></style>
