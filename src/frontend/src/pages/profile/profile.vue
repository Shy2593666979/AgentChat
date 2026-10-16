<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import UiIcon from '../../components/UiIcon.vue';
import UserAvatar from '../../components/UserAvatar.vue';
import { userAvatarUrl } from '../../utils/user-avatar';
import OverviewGlyph from '../../components/OverviewGlyph.vue';
import { useUserStore } from '../../store/user';
import { getUserInfoAPI, updateUserInfoAPI } from '../../apis/auth';
import { uploadFileAPI } from '../../apis/tool';
import { getConversationListAPI } from '../../apis/history';
import { getAgentsAPI } from '../../apis/agent';
import { getKnowledgeListAPI } from '../../apis/knowledge';
import { formatDataDate, safeResourceUrl } from '../../utils/data-pages';
import { responseError } from '../../utils/resource-visuals';
const store = useUserStore();
const loading = ref(false), loadError = ref(''), saving = ref(false), saveError = ref(''), user = ref<Record<string, any>>();
const description = ref(store.userInfo?.description || ''), savedDescription = ref(description.value), avatar = ref(store.userInfo?.avatar || '');
const avatarDialog = ref(false), avatarSaving = ref(false), avatarUploading = ref(false), avatarError = ref(''), chosenAvatar = ref(''), brokenImages = ref(new Set<string>());
const counts = reactive({ dialogs: undefined as number | undefined, agents: undefined as number | undefined, documents: undefined as number | undefined }), statsLoading = ref(false), statsError = ref(false);
let disposed = false, requestId = 0;
const username = computed(() => user.value?.user_name || user.value?.username || store.userInfo?.username || '用户');
const email = computed(() => user.value?.user_email || user.value?.email || '');
const role = computed(() => store.userInfo?.id === '1' ? '管理员' : '用户');
const accountStatus = computed(() => typeof user.value?.delete === 'boolean' ? (user.value.delete ? '已停用' : '正常') : '—');
const stats = computed(() => [{ label: '会话记录', value: counts.dialogs ?? '—', hint: '已保存的智能体会话记录', icon: 'chat', theme: 'blue' }, { label: '创建智能体', value: counts.agents ?? '—', hint: '当前账号创建的智能体数量', icon: 'bot', theme: 'purple' }, { label: '知识库文档', value: counts.documents ?? '—', hint: '当前账号可见知识库中的文档', icon: 'book', theme: 'green' }, { label: '账户状态', value: accountStatus.value, hint: accountStatus.value === '正常' ? '账户运行状态良好' : accountStatus.value === '已停用' ? '当前账户已停用' : '暂无账户状态信息', icon: 'check', theme: 'orange' }]);
const validImage = (url: string) => !!userAvatarUrl(url) && !brokenImages.value.has(url);
function failImage(url: string) { brokenImages.value = new Set([...brokenImages.value, url]); }
async function loadUser() { const id = ++requestId; loading.value = true; loadError.value = ''; try {
    if (!store.userInfo?.id)
        throw new Error('未读取到当前账号信息，请重新登录');
    const response = await getUserInfoAPI(store.userInfo.id);
    if (disposed || id !== requestId)
        return;
    if (response.data.status_code !== 200 || !response.data.data)
        throw new Error(response.data.status_message || '用户信息加载失败');
    const info = response.data.data;
    user.value = info;
    avatar.value = info.user_avatar || info.avatar || '';
    description.value = info.user_description ?? info.description ?? '';
    savedDescription.value = description.value;
    store.updateUserInfo({ username: info.user_name || info.username || username.value, avatar: avatar.value, description: description.value });
}
catch (error) {
    if (!disposed && id === requestId)
        loadError.value = responseError(error, '用户信息加载失败，请重试');
}
finally {
    if (!disposed && id === requestId)
        loading.value = false;
} }
async function loadStats() { statsLoading.value = true; statsError.value = false; const results = await Promise.allSettled([getConversationListAPI(), getAgentsAPI(), getKnowledgeListAPI()]); if (disposed)
    return; const [dialogs, agents, knowledge] = results; if (dialogs.status === 'fulfilled' && dialogs.value.data.status_code === 200 && Array.isArray(dialogs.value.data.data))
    counts.dialogs = dialogs.value.data.data.length;
else {
    counts.dialogs = undefined;
    statsError.value = true;
} if (agents.status === 'fulfilled' && agents.value.data.status_code === 200 && Array.isArray(agents.value.data.data))
    counts.agents = agents.value.data.data.filter((agent: any) => String(agent.user_id) === store.userInfo?.id).length;
else {
    counts.agents = undefined;
    statsError.value = true;
} if (knowledge.status === 'fulfilled' && knowledge.value.data.status_code === 200 && Array.isArray(knowledge.value.data.data))
    counts.documents = knowledge.value.data.data.reduce((sum: number, item: any) => sum + Number(item.count || 0), 0);
else {
    counts.documents = undefined;
    statsError.value = true;
} statsLoading.value = false; }
async function saveProfile() { if (saving.value || avatarSaving.value || !store.userInfo?.id)
    return; saveError.value = ''; if (description.value.length > 200) {
    saveError.value = '个人简介不能超过 200 字符';
    return;
} saving.value = true; const value = description.value; try {
    const response = await updateUserInfoAPI(store.userInfo.id, avatar.value, value);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '保存失败');
    savedDescription.value = value;
    store.updateUserInfo({ description: value });
    ElMessage.success('个人资料已保存');
}
catch (error) {
    saveError.value = responseError(error, '个人资料保存失败');
}
finally {
    saving.value = false;
} }
function openAvatars() { chosenAvatar.value = userAvatarUrl(avatar.value); avatarError.value = ''; avatarDialog.value = true; }
async function uploadAvatar(event: Event) { const input = event.target as HTMLInputElement, file = input.files?.[0]; input.value = ''; if (!file)
    return; if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 2 * 1024 * 1024) {
    avatarError.value = '请选择 2MB 以内的 JPG 或 PNG 图片';
    return;
} avatarUploading.value = true; avatarError.value = ''; try {
    const response = await uploadFileAPI(file);
    if (response.data.status_code !== 200 || typeof response.data.data !== 'string' || !safeResourceUrl(response.data.data))
        throw new Error(response.data.status_message || '头像上传失败');
    chosenAvatar.value = response.data.data;
    ElMessage.success('头像已上传，请保存');
}
catch (error) {
    avatarError.value = responseError(error, '头像上传失败');
}
finally {
    avatarUploading.value = false;
} }
async function saveAvatar() { if (avatarSaving.value || avatarUploading.value || saving.value || !store.userInfo?.id || (chosenAvatar.value !== '' && !validImage(chosenAvatar.value)))
    return; avatarSaving.value = true; avatarError.value = ''; const value = chosenAvatar.value; try {
    const response = await updateUserInfoAPI(store.userInfo.id, value, savedDescription.value);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '头像保存失败');
    avatar.value = value;
    store.updateUserInfo({ avatar: value });
    avatarDialog.value = false;
    ElMessage.success('头像已更新');
}
catch (error) {
    avatarError.value = responseError(error, '头像保存失败');
}
finally {
    avatarSaving.value = false;
} }
onBeforeRouteLeave(async () => { if (saving.value || avatarSaving.value || avatarUploading.value)
    return false; if (description.value === savedDescription.value)
    return true; try {
    await ElMessageBox.confirm('个人简介有未保存的修改，是否放弃？', '未保存的修改', { confirmButtonText: '放弃修改', cancelButtonText: '继续编辑' });
    return true;
}
catch {
    return false;
} });
onMounted(() => { store.initUserState(); loadUser(); loadStats(); });
onBeforeUnmount(() => { disposed = true; requestId++; });
</script>
<template><div class="b3-page b4-page b4-profile"><div class="profile-decoration" aria-hidden="true"><svg viewBox="0 0 1400 210" fill="none"><defs><linearGradient id="profileCube" x2="1" y2="1"><stop stop-color="#aed5ff"/><stop offset="1" stop-color="#d4eeff"/></linearGradient><radialGradient id="profilePlanet"><stop stop-color="#d5e8ff"/><stop offset=".65" stop-color="#8cb8ff"/><stop offset="1" stop-color="#b8dcff"/></radialGradient></defs><path d="m12 82 56-25 67 24-59 29Zm0 0v54l64 26v-52m0 0 59-29v55l-59 26" fill="url(#profileCube)" stroke="#eef8ff"/><path d="m32 33 10-4 13 4-10 5Zm0 0v13l13 6V38m0 0 10-5v14l-10 5" fill="url(#profileCube)"/><path d="m79 171 223-95 152 44-205 77" fill="#d7ecff" opacity=".35"/><circle cx="1180" cy="100" r="58" fill="url(#profilePlanet)" stroke="white" stroke-width="2"/><ellipse cx="1180" cy="108" rx="91" ry="16" transform="rotate(-20 1180 108)" stroke="#f5fcff" stroke-width="5"/><path d="m1120 177 208-83 70 32-211 75" fill="#b2d3ff" opacity=".3"/></svg></div><div class="profile-layout"><header class="data-heading"><div class="heading-copy"><h1>个人中心</h1><p>管理你的个人信息和账户设置</p></div></header><div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button @click="loadUser">重新加载</button></div><section class="profile-columns" v-loading="loading"><article class="data-surface identity-card"><h2>用户信息</h2><p class="panel-subtitle">你的账户基本信息</p><div class="identity-body"><span class="profile-avatar"><UserAvatar :username="username" :src="avatar"/></span><h3>{{username}}</h3><span class="role-badge">{{role}}</span><p class="registration-date"><UiIcon name="clock"/>注册时间 <span>{{formatDataDate(user?.create_time,false)}}</span></p><el-button class="change-avatar" :disabled="saving||loading" @click="openAvatars"><UiIcon name="camera"/>更换头像</el-button></div></article><article class="data-surface profile-form"><h2>基本资料</h2><p class="panel-subtitle">完善个人资料，便于他人了解你</p><el-form label-position="top" :disabled="loading||saving||avatarSaving"><el-form-item label="用户名"><el-input :model-value="username" readonly aria-label="用户名，仅供查看"/></el-form-item><el-form-item label="个人简介"><el-input v-model="description" type="textarea" :rows="4" maxlength="200" show-word-limit placeholder="介绍一下你自己吧，让更多人了解你"/></el-form-item><el-form-item label="邮箱"><el-input :model-value="email" readonly :placeholder="loading?'加载中…':'未填写邮箱'" aria-label="邮箱，仅供查看"/></el-form-item><p class="account-field-hint">用户名和邮箱为账号信息，仅供查看。</p><p v-if="saveError" class="dialog-error" role="alert">{{saveError}}</p><el-button type="primary" class="save-profile" :loading="saving" :disabled="loading||avatarSaving||description===savedDescription" @click="saveProfile">保存修改</el-button></el-form></article></section><section class="data-surface profile-overview" v-loading="statsLoading"><header><div><h2>使用概览</h2><p class="panel-subtitle">你在agentchat的使用情况</p></div><button v-if="statsError" class="stats-retry" @click="loadStats">部分数据加载失败 · 重试</button></header><div class="overview-grid"><article v-for="stat in stats" :key="stat.label" class="overview-card" :class="stat.theme"><span class="overview-icon"><OverviewGlyph :name="stat.icon"/></span><div><h3>{{stat.label}}</h3><strong :class="{normal:stat.label==='账户状态'&&stat.value==='正常'}">{{stat.value}}</strong><p>{{stat.hint}}</p></div></article></div></section></div>
<el-dialog v-model="avatarDialog" title="更换头像" width="440px" class="b4-dialog" append-to-body :close-on-click-modal="false" :close-on-press-escape="!avatarSaving&&!avatarUploading" :show-close="!avatarSaving&&!avatarUploading"><div class="avatar-preview"><UserAvatar :username="username" :src="chosenAvatar"/></div><p class="avatar-default-note">默认使用用户名首字母，也可上传你的专属头像。</p><label class="avatar-upload" :class="{disabled:avatarSaving||avatarUploading}"><UiIcon name="upload"/>{{avatarUploading?'上传中…':'上传 JPG / PNG 图片'}}<input type="file" accept="image/jpeg,image/png" :disabled="avatarSaving||avatarUploading" @change="uploadAvatar"></label><p class="avatar-help">图片不超过 2MB，上传后点击保存头像。</p><button v-if="chosenAvatar" class="avatar-reset" :disabled="avatarSaving||avatarUploading" @click="chosenAvatar='';avatarError=''">恢复字母头像</button><p v-if="avatarError" class="dialog-error" role="alert">{{avatarError}}</p><template #footer><el-button :disabled="avatarSaving||avatarUploading" @click="avatarDialog=false">取消</el-button><el-button type="primary" :loading="avatarSaving" :disabled="avatarUploading||(!!chosenAvatar&&!validImage(chosenAvatar))" @click="saveAvatar">保存头像</el-button></template></el-dialog>
</div></template>
<style scoped src="./profile.css"></style>
