<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import UiIcon from '../../components/UiIcon.vue'
import { useUserStore } from '../../store/user'
import ProviderLogo from '../../components/ProviderLogo.vue'
import { modelProviders, modelProviderDisplayName } from '../../utils/model-provider-brand'
import { createLLMAPI, updateLLMAPI, getVisibleLLMsAPI, type LLMResponse, type CreateLLMRequest } from '../../apis/llm'

const route = useRoute(), router = useRouter(), userStore = useUserStore()
const modelId = computed(() => typeof route.query.id === 'string' ? route.query.id : '')
const loading = ref(false), saving = ref(false), loadError = ref(''), saveError = ref('')
const currentModel = ref<LLMResponse>(), formRef = ref<FormInstance>()
const isEditing = computed(() => !!modelId.value), official = computed(() => currentModel.value?.user_id === '0')
const canRenameBuiltin=computed(()=>official.value&&userStore.userInfo?.id==='1')
const form = reactive<CreateLLMRequest>({ model:'', show_model:'', llm_type:'LLM', provider:'', base_url:'', api_key:'' })
const types = [{ value:'LLM', label:'对话模型' },{ value:'Embedding', label:'向量模型' },{ value:'Rerank', label:'重排模型' }]
const providers = modelProviders
const rules: FormRules = {
  model:[{ required:true, whitespace:true, message:'请输入模型名称或标识', trigger:'blur' }],
  llm_type:[{ required:true, message:'请选择模型类型', trigger:'change' }],
  provider:[{ required:true, whitespace:true, message:'请输入服务提供方', trigger:'change' }],
  api_key:[{ required:true, whitespace:true, message:'请输入 API Key', trigger:'blur' }],
  base_url:[{ required:true, message:'请输入 API Base URL', trigger:'blur' },{ validator:(_rule,value,callback) => {
    try { if (!['http:','https:'].includes(new URL(value).protocol)) throw new Error(); callback() }
    catch { callback(new Error('请输入以 http:// 或 https:// 开头的有效地址')) }
  }, trigger:'blur' }]
}
let requestId = 0
async function fetchModel() {
  const id = ++requestId, requestedModelId = modelId.value
  loading.value = !!requestedModelId; loadError.value = ''; saveError.value = ''; currentModel.value = undefined
  Object.assign(form, { model:'', show_model:'', llm_type:'LLM', provider:'', base_url:'', api_key:'' })
  if (!requestedModelId) return
  try {
    const response = await getVisibleLLMsAPI()
    if (id !== requestId) return
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '模型信息加载失败')
    const data = response.data.data || {}
    const models = Array.isArray(data) ? data : Object.values(data).flat()
    const model = models.find(item => item.llm_id === requestedModelId)
    if (!model) throw new Error('未找到此模型，请返回列表确认')
    currentModel.value = model
    Object.assign(form, { model:model.model, show_model:model.show_model||'', llm_type:model.llm_type, provider:modelProviderDisplayName(model.provider), base_url:model.base_url, api_key:model.api_key })
  } catch (error:any) { if (id === requestId) loadError.value = error.message || '模型信息加载失败，请重试' }
  finally { if (id === requestId) loading.value = false }
}
async function saveModel() {
  if (loading.value || saving.value || (official.value&&!canRenameBuiltin.value) || (isEditing.value && !currentModel.value)) return
  saving.value = true; saveError.value = ''
  try {
    if (!official.value&&!await formRef.value?.validate().catch(() => false)) return
    const data = { ...form, model:form.model.trim(), show_model:(form.show_model||'').trim(), provider:form.provider.trim(), base_url:form.base_url.trim(), api_key:form.api_key.trim() }
    const response = official.value ? await updateLLMAPI({llm_id:modelId.value,show_model:(form.show_model||'').trim()}) : isEditing.value ? await updateLLMAPI({ llm_id:modelId.value, ...data }) : await createLLMAPI(data)
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '保存失败')
    ElMessage.success(isEditing.value ? '模型配置已更新' : '模型已添加'); await router.push('/model')
  } catch (error:any) { saveError.value = typeof error.response?.data?.detail === 'string' ? error.response.data.detail : error.message || '保存失败，请重试' }
  finally { saving.value = false }
}
watch(modelId, fetchModel, { immediate:true })
</script>
<template>
  <div class="b3-page b3-model-editor" v-loading="loading">
    <div class="editor-layout"><header class="data-heading"><div class="heading-copy"><h1>{{ isEditing ? '编辑模型' : '添加模型' }}</h1><p>配置模型服务与访问参数。</p></div></header>
      <div v-if="loadError" class="error-banner" role="alert"><span>{{ loadError }}</span><button @click="fetchModel">重新加载</button></div>
      <div v-if="!isEditing || currentModel" class="editor-columns">
        <el-form ref="formRef" :model="form" :rules="rules" :disabled="saving || (official&&!canRenameBuiltin)" label-position="left" label-width="194px" require-asterisk-position="right" class="data-surface model-form">
          <h2>基础信息</h2><el-form-item label="展示名称" prop="show_model"><el-input v-model="form.show_model" maxlength="128" show-word-limit placeholder="例如 豆包 Pro，留空使用模型标识"/><p class="field-help">用于模型列表、智能体卡片和模型选择；不影响实际调用。</p></el-form-item><el-form-item label="模型名称 / 标识" prop="model"><el-input :disabled="official" v-model="form.model" placeholder="例如 gpt-4o"/><p class="field-help">填写服务提供方的实际模型标识，用于管理和调用此模型。</p></el-form-item>
          <el-form-item label="模型类型" prop="llm_type"><el-select :disabled="official" v-model="form.llm_type" style="width:100%"><template #prefix><UiIcon :name="form.llm_type === 'LLM' ? 'chat' : form.llm_type === 'Embedding' ? 'layers' : 'chart'"/></template><el-option v-for="type in types" :key="type.value" :label="type.label" :value="type.value"/></el-select><p class="field-help">选择模型的能力类型。</p></el-form-item>
          <el-form-item label="服务提供方" prop="provider"><el-select :disabled="official" v-model="form.provider" filterable allow-create default-first-option style="width:100%" placeholder="选择或输入提供方"><template v-if="form.provider" #prefix><ProviderLogo :provider="form.provider" :base-url="form.base_url"/></template><el-option v-for="provider in providers" :key="provider" :label="provider" :value="provider"><span class="provider-option"><ProviderLogo :provider="provider"/>{{provider}}</span></el-option></el-select><p class="field-help">选择提供方，或输入已有服务对应的名称。</p></el-form-item>
          <hr><h2>连接配置</h2><el-form-item label="API Base URL" prop="base_url"><el-input :disabled="official" v-model="form.base_url" placeholder="https://api.example.com/v1"/><p class="field-help">模型服务的接口地址，通常以 http(s):// 开头。</p></el-form-item>
          <el-form-item label="API Key" prop="api_key"><el-input :disabled="official" v-model="form.api_key" type="password" show-password autocomplete="off" placeholder="请输入 API Key"/><p class="field-help">用于访问模型服务的密钥。</p></el-form-item>
          <p class="model-notice"><UiIcon name="info"/>{{ official ? (canRenameBuiltin ? '内置模型可修改展示名称，连接配置仅供查看。' : '内置模型由平台维护，当前配置仅供查看。') : '请确保接口地址与模型标识正确。' }}</p>
          <p v-if="saveError" class="save-error" role="alert">{{ saveError }}</p><div class="form-actions"><el-button :disabled="saving" @click="router.push('/model')">{{ official ? '返回' : '取消' }}</el-button><el-button v-if="!official||canRenameBuiltin" type="primary" :loading="saving" @click="saveModel">保存模型</el-button></div>
        </el-form>
        <aside class="data-surface model-instructions"><h2><UiIcon name="file"/>配置说明</h2><div v-for="(step,index) in [{title:'选择合适的模型类型',copy:'根据业务场景选择对话模型、嵌入模型或重排模型。'},{title:'填写正确的连接信息',copy:'请填写服务提供方的 API Base URL 和有效的 API Key，确保网络可正常访问。'},{title:'验证并保存',copy:'确认配置信息无误后，点击保存模型。保存后即可在会话或智能体中使用该模型。'}]" :key="step.title" class="instruction-step"><span>{{ index + 1 }}</span><div><h3>{{ step.title }}</h3><p>{{ step.copy }}</p></div></div></aside>
      </div>
    </div>
  </div>
</template>
<style scoped src="./model-editor.css"></style>
