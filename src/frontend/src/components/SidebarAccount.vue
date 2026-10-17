<script setup lang="ts">
import {useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {useUserStore} from '../store/user';
import {logoutAPI} from '../apis/auth';
import UserAvatar from './UserAvatar.vue';
import TopUtility from './TopUtility.vue';
import UiIcon from './UiIcon.vue';
defineProps<{collapsed:boolean}>();
const emit=defineEmits<{toggle:[]}>();
const user=useUserStore(),router=useRouter();
async function command(value:string){if(value==='profile'){router.push('/profile');return;}if(value==='logout'){try{await logoutAPI()}catch{} user.logout();ElMessage.success('已退出登录');router.push('/login');}}
</script>
<template><div class="sidebar-account"><el-dropdown trigger="click" placement="top-start" :teleported="true" popper-class="sidebar-account-menu" @command="command"><button class="sidebar-account-button" aria-label="账户菜单"><span class="sidebar-account-avatar"><UserAvatar :username="user.userInfo?.username" :src="user.userInfo?.avatar"/></span><span class="sidebar-account-name"><strong>{{user.userInfo?.nickname||user.userInfo?.username||'我的账户'}}</strong><small>个人中心</small></span></button><template #dropdown><el-dropdown-menu><el-dropdown-item command="profile"><UiIcon name="user"/>个人资料</el-dropdown-item><el-dropdown-item command="logout" divided><UiIcon name="external"/>退出登录</el-dropdown-item></el-dropdown-menu></template></el-dropdown><TopUtility placement="top-start"/><button class="sidebar-account-collapse" :aria-label="collapsed?'展开侧边栏':'收起侧边栏'" :title="collapsed?'展开侧边栏':'收起侧边栏'" @click="emit('toggle')"><UiIcon :name="collapsed?'chevrons-right':'chevrons-left'"/></button></div></template>
<style scoped>.sidebar-account{display:flex;align-items:center;gap:6px;height:52px;border-top:1px solid #e4edf8;padding:8px 4px 0}.sidebar-account :deep(.el-dropdown){flex:1;min-width:0}.sidebar-account-button{display:flex;align-items:center;gap:10px;min-width:0;max-width:100%;background:transparent;border:0;padding:0;cursor:pointer;color:#23365b;text-align:left}.sidebar-account-avatar{width:36px;height:36px;flex:none;display:grid;place-items:center;background:#eaf2ff;border:1px solid #dfebfc;border-radius:50%;overflow:hidden}.sidebar-account-avatar img{width:100%;height:100%;object-fit:cover}.sidebar-account-avatar .p-icon{width:22px;height:22px}.sidebar-account-name{min-width:0}.sidebar-account-name strong{display:block;max-width:95px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;font-weight:600}.sidebar-account-name small{display:block;font-size:11px;color:#8997af;margin-top:2px}.sidebar-account-collapse{display:grid;place-items:center;width:27px;height:32px;flex:none;background:transparent;border:0;color:#6f80a2;cursor:pointer;padding:0}.sidebar-account-collapse .p-icon{width:20px;height:20px}.sidebar-account :deep(.s-notification-button){width:30px;height:32px;margin:0;padding:4px}.sidebar-account :deep(.s-notification-button .p-icon){width:22px;height:22px}:global(body[data-sidebar-collapsed='true'] .sidebar-account),:global(body[data-design='screenshot'] .s-sidebar-collapsed .sidebar-account){height:auto;flex-direction:column;gap:10px;padding-top:12px}:global(body[data-sidebar-collapsed='true'] .sidebar-account-name){display:none}:global(body[data-sidebar-collapsed='true'] .sidebar-account .el-dropdown){flex:none}@media(max-width:700px){.sidebar-account{height:auto;flex-direction:column;gap:10px;padding-top:12px}.sidebar-account-name{display:none}.sidebar-account :deep(.el-dropdown){flex:none}}</style>

<style>
.sidebar-account-menu.el-popper{min-width:174px;border:1px solid #dfe9fa;border-radius:12px;box-shadow:0 8px 28px #17345b1a}
.sidebar-account-menu .el-dropdown-menu{padding:6px;border-radius:12px}
.sidebar-account-menu .el-dropdown-menu__item{gap:10px;padding:10px 12px;color:#334d74;border-radius:7px;font-family:var(--ac-font)}
.sidebar-account-menu .el-dropdown-menu__item .p-icon{width:18px;height:18px;color:#6683ac}
.sidebar-account-menu .el-dropdown-menu__item:not(.is-disabled):hover{background:#edf4ff;color:#246bff}
</style>
