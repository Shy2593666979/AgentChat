<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerAPI } from '../../apis/auth'
import type { RegisterForm } from '../../apis/auth'
import BrandLogo from '../../components/BrandLogo.vue'

const router = useRouter()

const registerForm = reactive<RegisterForm>({
  user_name: '',
  user_email: '',
  user_password: ''
})

const confirmPassword = ref('')
const loading = ref(false)
const registerError = ref('')

const validateForm = () => {
  if (!registerForm.user_name) {
    registerError.value = '请输入用户名'
    return false
  }

  if (registerForm.user_name.length > 20) {
    registerError.value = '用户名长度不应该超过20个字符'
    return false
  }

  if (!registerForm.user_password) {
    registerError.value = '请输入密码'
    return false
  }

  if (registerForm.user_password.length < 6) {
    registerError.value = '密码长度至少6个字符'
    return false
  }

  if (registerForm.user_password !== confirmPassword.value) {
    registerError.value = '两次输入的密码不一致'
    return false
  }

  if (registerForm.user_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.user_email)) {
    registerError.value = '请输入有效的邮箱地址'
    return false
  }

  return true
}

const handleRegister = async () => {
  if (loading.value) return
  registerError.value = ''
  if (!validateForm()) {
    return
  }

  try {
    loading.value = true
    const response = await registerAPI(registerForm)

    if (response.data.status_code === 200) {
      ElMessage.success('注册成功，请登录')
      // 跳转到登录页面
      router.push('/login')
    } else {
      registerError.value = response.data.status_message || '注册失败'
    }
  } catch (error: any) {
    console.error('注册错误:', error)
    if (error.response?.data?.detail) {
      registerError.value = typeof error.response.data.detail === 'string' ? error.response.data.detail : '注册信息不符合要求，请检查后重试'
    } else {
      registerError.value = '注册失败，请检查网络连接'
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
const showRegisterPassword = ref(false)
const showConfirmPassword = ref(false)
</script>


<template><div class="converted-register"><svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;width:0;height:0;overflow:hidden"><defs>
<symbol id="icon-user" viewBox="0 0 24 24"><circle cx="12" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4 21v-2a8 6 0 0 1 16 0v2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
<symbol id="icon-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m4 7 8 6 8-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="icon-lock" viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="12" rx="3" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M7 10V7a5 5 0 0 1 10 0v3" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="12" cy="15.5" r="1.6" fill="currentColor"/><path d="M12 16v2" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="icon-eye-off" viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4 21 21 3" stroke="#fff" stroke-width="4"/><path d="M4 21 21 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
<symbol id="icon-eye" viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="icon-robot" viewBox="0 0 40 40"><path d="M20 6v7" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><rect x="5" y="13" width="30" height="26" rx="8" fill="currentColor"/><rect x="10" y="20" width="20" height="11" rx="5" fill="white"/><path d="M15 23v4m10-4v4" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M3 23v6m34-6v6" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></symbol>
<symbol id="icon-book" viewBox="0 0 40 40"><path d="M20 10c-4-4-10-4-15-2v24c6-2 11-1 15 3 4-4 9-5 15-3V8c-5-2-11-2-15 2zM20 10v25" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/></symbol>
<symbol id="icon-grid" viewBox="0 0 40 40"><g fill="none" stroke="currentColor" stroke-width="3.1"><rect x="6" y="5" width="12" height="12" rx="4"/><rect x="24" y="5" width="12" height="12" rx="4"/><rect x="6" y="23" width="12" height="12" rx="4"/><rect x="24" y="23" width="12" height="12" rx="4"/></g></symbol>
</defs></svg><header class="header"><BrandLogo/></header><svg class="illustration" viewBox="0 0 960 520" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs>
<linearGradient id="floor" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c9e4ff" stop-opacity=".55"/><stop offset="1" stop-color="#dfedff" stop-opacity=".2"/></linearGradient>
<linearGradient id="front" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#8fbdff" stop-opacity=".65"/><stop offset="1" stop-color="#c3e2ff" stop-opacity=".18"/></linearGradient>
<linearGradient id="side" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#b4edff" stop-opacity=".7"/><stop offset="1" stop-color="#73b1ff" stop-opacity=".34"/></linearGradient>
<linearGradient id="top" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#b5d9ff" stop-opacity=".58"/><stop offset=".5" stop-color="#dcf7ff" stop-opacity=".85"/><stop offset="1" stop-color="#b8ddff" stop-opacity=".52"/></linearGradient>
<radialGradient id="planet" cx=".35" cy=".25" r=".8"><stop stop-color="#bad5ff"/><stop offset=".35" stop-color="#8fb8ff"/><stop offset=".7" stop-color="#6b9cfc"/><stop offset=".88" stop-color="#a4c5ff"/><stop offset="1" stop-color="#eaf3ff"/></radialGradient>
<radialGradient id="glass" cx=".4" cy=".45" r=".56"><stop offset=".55" stop-color="#fff" stop-opacity="0"/><stop offset=".87" stop-color="#fff" stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></radialGradient>
<linearGradient id="ring" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".95"/><stop offset=".45" stop-color="#c7e5ff" stop-opacity=".3"/><stop offset="1" stop-color="#83b3ff" stop-opacity=".8"/></linearGradient>
<filter id="blur"><feGaussianBlur stdDeviation="9"/></filter><filter id="soft"><feGaussianBlur stdDeviation="3"/></filter>
<clipPath id="planetclip"><circle cx="521" cy="299" r="110"/></clipPath>
</defs>
<g opacity=".72"><path d="M0 73 111 17 166 37 51 94z" fill="url(#floor)"/><path d="m0 73 51 21 114-57-1 79L0 180z" fill="url(#floor)"/><path d="m0 202 206-85 168 133-238 88L0 271z" fill="url(#top)"/><path d="m136 338 238-88v93l-238 94z" fill="url(#side)"/><path d="M0 271 136 338v45L0 324z" fill="url(#front)"/><path d="m0 364 404-167 440 198-405 160z" fill="url(#floor)"/><path d="m238 404 241-102 326 100-301 118z" fill="url(#front)"/><path d="m567 332 276-120 117 56-264 125z" fill="url(#floor)"/><path d="M0 504 204 420l222 92-188 82z" fill="url(#floor)"/><path d="m0 73 166 76 120-47L91 17z" fill="#e8f5ff" opacity=".32"/><path d="m0 181 275-109 121 57L0 302z" fill="#fff" opacity=".2"/><path d="M0 271 136 338l238-88" stroke="#fff" stroke-width="1.6" fill="none" opacity=".7"/></g>
<g><path d="m130 167 80-27 81 30-84 32z" fill="url(#top)"/><path d="m130 167 77 35v89l-77-35z" fill="url(#front)"/><path d="m207 202 84-32v88l-84 33z" fill="url(#side)"/><path d="m131 167 76 35 84-32m-84 32v89" fill="none" stroke="#fff" stroke-opacity=".65" stroke-width="1.6"/></g>
<g opacity=".85"><path d="m322 148 23-8 24 10-23 9z" fill="url(#top)"/><path d="m322 148 24 11v32l-24-10z" fill="url(#front)"/><path d="m346 159 23-9v31l-23 10z" fill="url(#side)"/><path d="m322 148 24 11 23-9m-23 9v32" stroke="#fff" stroke-opacity=".5" fill="none"/></g>
<g opacity=".9"><path d="m779 319 23-9 23 10-23 9z" fill="url(#top)"/><path d="m779 319 23 10v32l-23-10z" fill="url(#front)"/><path d="m802 329 23-9v31l-23 10z" fill="url(#side)"/><path d="m779 319 23 10 23-9m-23 9v32" stroke="#fff" stroke-opacity=".5" fill="none"/></g>
<ellipse cx="520" cy="422" rx="120" ry="24" fill="#80b1ff" opacity=".08" filter="url(#blur)"/>
<g transform="rotate(-24 518 299)"><ellipse cx="518" cy="299" rx="200" ry="38" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="3"/><ellipse cx="518" cy="302" rx="183" ry="26" fill="none" stroke="url(#ring)" stroke-width="10" opacity=".7"/></g>
<circle cx="521" cy="299" r="110" fill="url(#planet)"/>
<g clip-path="url(#planetclip)" filter="url(#blur)" opacity=".53" fill="#e7f2ff"><path d="m416 248 26-42 46-12 12 15-19 31-28 8-4 31-29 15-9-17z"/><path d="m469 207 36-18 70 15 38 39-31 10-26-25-42-3-15 13-17-6z"/><path d="m416 318 28-27 19 17-13 34 15 15-10 34-31-27z"/><path d="m582 258 41-1 33 51-16 51-26 20-32-15 15-28-14-38z"/><path d="m453 384 34-8 22 8 12 18 45-5 33-26 16 18-23 28-61 11-61-17z"/></g>
<g clip-path="url(#planetclip)" fill="#5b8de8" opacity=".2" filter="url(#soft)"><path d="m438 260 14-14 24 4-8 17-20 8z"/><path d="m491 218 23-8 19 8-12 9-13-5z"/><path d="m429 308 11-10 16 14-6 17-17-3z"/><path d="m526 359 20-18 13 4-8 18-15 6z"/><path d="m560 238 17 7 13-3 16 19-19 4-11-12z"/></g>
<circle cx="521" cy="299" r="110" fill="url(#glass)" stroke="#fff" stroke-width="2.5" stroke-opacity=".85"/>
<g transform="rotate(-24 518 299)"><path d="M318 299a200 38 0 0 0 400 0l-17 0a183 26 0 0 1-366 0z" fill="url(#ring)" stroke="#ffffff" stroke-opacity=".8" stroke-width="1.7"/><path d="M323 310c37 41 347 41 390-1" fill="none" stroke="#8cbbff" stroke-opacity=".3" stroke-width="3"/><path d="M335 299a183 26 0 0 0 366 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-opacity=".9"/></g>
</svg><main class="main"><section class="hero" aria-labelledby="hero-title"><h1 id="hero-title">开启你的 <span>AI 工作空间</span></h1><p class="hero-description">整合知识、工具与智能体，让 AI 成为你的超级生产力伙伴<br>从思考到执行，助力更高效的工作与创造。</p><div class="features"><div class="feature"><span class="feature-icon"><svg aria-hidden="true"><use href="#icon-robot"/></svg></span><div><div class="feature-title">智能体</div><div class="feature-description">定制专属 AI 助手</div></div></div><div class="feature"><span class="feature-icon"><svg aria-hidden="true"><use href="#icon-book"/></svg></span><div><div class="feature-title">知识库</div><div class="feature-description">汇聚企业知识</div></div></div><div class="feature"><span class="feature-icon"><svg aria-hidden="true"><use href="#icon-grid"/></svg></span><div><div class="feature-title">工具</div><div class="feature-description">连接更多能力</div></div></div></div></section><section class="register-card" aria-labelledby="card-title"><h2 id="card-title">创建账号</h2><p class="card-subtitle">注册 agentchat，开启你的 AI 工作空间</p><form :aria-busy="loading" @submit.prevent="handleRegister"><div class="field"><label for="register-user">用户名</label><div class="input-wrap"><svg aria-hidden="true"><use href="#icon-user"/></svg><input id="register-user" v-model="registerForm.user_name" placeholder="请输入用户名" autocomplete="username" maxlength="20" aria-describedby="register-user-help" required></div><p id="register-user-help" class="field-help">用户名不超过 20 个字符</p></div><div class="field"><label for="register-email">邮箱（可选）</label><div class="input-wrap"><svg aria-hidden="true"><use href="#icon-mail"/></svg><input id="register-email" v-model="registerForm.user_email" type="email" placeholder="请输入邮箱" autocomplete="email"></div></div><div class="field"><label for="register-password">密码</label><div class="input-wrap"><svg aria-hidden="true"><use href="#icon-lock"/></svg><input id="register-password" v-model="registerForm.user_password" :type="showRegisterPassword?'text':'password'" placeholder="请输入密码" autocomplete="new-password" minlength="6" aria-describedby="register-password-help" required><button class="toggle-password" type="button" :aria-label="showRegisterPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showRegisterPassword" aria-controls="register-password" @click="showRegisterPassword=!showRegisterPassword"><svg aria-hidden="true"><use :href="showRegisterPassword ? '#icon-eye' : '#icon-eye-off'"/></svg></button></div><p id="register-password-help" class="field-help">密码至少 6 个字符</p></div><div class="field confirm"><label for="register-confirm">确认密码</label><div class="input-wrap"><svg aria-hidden="true"><use href="#icon-lock"/></svg><input id="register-confirm" v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" placeholder="请再次输入密码" autocomplete="new-password" aria-describedby="register-confirm-help" required><button class="toggle-password" type="button" :aria-label="showConfirmPassword ? '隐藏确认密码' : '显示确认密码'" :aria-pressed="showConfirmPassword" aria-controls="register-confirm" @click="showConfirmPassword = !showConfirmPassword"><svg aria-hidden="true"><use :href="showConfirmPassword ? '#icon-eye' : '#icon-eye-off'"/></svg></button></div><p id="register-confirm-help" class="field-help">请确保两次输入的密码一致</p></div><p v-if="registerError" class="auth-error" role="alert">{{ registerError }}</p><button class="register-button" type="submit" :disabled="loading">{{loading?'注册中…':'注册'}}</button></form><div class="login-footer"><span>已有账号？<button type="button" @click="goToLogin">立即登录</button></span></div></section></main></div></template>
<style scoped src="./auth-entry.css"></style>
