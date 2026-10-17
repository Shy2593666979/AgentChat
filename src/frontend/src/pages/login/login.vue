<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginAPI, getUserInfoAPI } from '../../apis/auth'
import { useUserStore } from '../../store/user'
import BrandLogo from '../../components/BrandLogo.vue'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: localStorage.getItem('agentchat.rememberedUsername') || '',
  password: ''
})

const rememberUsername = ref(localStorage.getItem('agentchat.rememberUsername') !== 'false')
const loading = ref(false)
const loginError = ref('')

const handleLogin = async () => {
  if (loading.value) return
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    loginError.value = ''
    loading.value = true
    const response = await loginAPI(loginForm)

    // response.data结构可能是{status_code: number, data: {...}}
    const responseData = response.data
    if (responseData.status_code === 200) {
      ElMessage.success('登录成功')
      localStorage.setItem('agentchat.rememberUsername', String(rememberUsername.value))
      if (rememberUsername.value) localStorage.setItem('agentchat.rememberedUsername', loginForm.username)
      else localStorage.removeItem('agentchat.rememberedUsername')

      // 使用store管理用户状态
      const userData = responseData.data
      if (userData?.access_token && userData.user_id) {
        // 先保存基础用户信息
        userStore.setUserInfo(userData.access_token, {
          id: userData.user_id,
          username: loginForm.username
        })

        // 立即获取完整的用户信息（包括头像等）
        try {
          const userInfoResponse = await getUserInfoAPI(userData.user_id)
          const userInfoData = userInfoResponse.data
          if (userInfoData.status_code === 200) {
            const completeUserData = userInfoData.data || {}
            // 更新用户信息，包含头像
            userStore.updateUserInfo({
              avatar: completeUserData.user_avatar || completeUserData.avatar,
              description: completeUserData.user_description || completeUserData.description
            })
          }
        } catch (error) {
          console.error('获取用户详细信息失败:', error)
        }
      }

      // 跳转到主页
      router.push('/')
    } else {
      loginError.value = responseData.status_message || '登录失败'
    }
  } catch (error: any) {
    console.error('登录错误:', error)
    const status = error.response?.status
    const data = error.response?.data
    if (!error.response || [500, 502, 503, 504].includes(status)) {
      loginError.value = '登录服务暂时无法连接或处理请求，请确认后端已启动、API 地址配置正确。'
    } else {
      const message = data?.status_message || data?.message || data?.detail
      loginError.value = typeof message === 'string' ? message : '登录失败，请检查账号和密码'
    }
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
const showLoginPassword=ref(false)
</script>


<template><div class="converted-login page"><header class="brand"><BrandLogo/></header><main class="layout"><section class="hero" aria-labelledby="hero-title">
<svg class="art" viewBox="0 0 1055 385" fill="none" aria-hidden="true">
<defs>
<linearGradient id="beam" x1="260" y1="30" x2="690" y2="345" gradientUnits="userSpaceOnUse"><stop stop-color="white" stop-opacity=".7"/><stop offset="1" stop-color="white" stop-opacity=".05"/></linearGradient>
<linearGradient id="cube-top" x1="115" y1="84" x2="334" y2="188" gradientUnits="userSpaceOnUse"><stop stop-color="#a9bdff" stop-opacity=".8"/><stop offset=".53" stop-color="#d0f1ff" stop-opacity=".7"/><stop offset="1" stop-color="#a5dfff" stop-opacity=".65"/></linearGradient>
<linearGradient id="cube-left" x1="107" y1="145" x2="242" y2="307" gradientUnits="userSpaceOnUse"><stop stop-color="#b6c9ff" stop-opacity=".75"/><stop offset="1" stop-color="#b5d1ff" stop-opacity=".33"/></linearGradient>
<linearGradient id="cube-right" x1="346" y1="145" x2="238" y2="296" gradientUnits="userSpaceOnUse"><stop stop-color="#8bd4ff" stop-opacity=".63"/><stop offset="1" stop-color="#c5d8ff" stop-opacity=".33"/></linearGradient>
<linearGradient id="small-top" x1="309" y1="28" x2="357" y2="47" gradientUnits="userSpaceOnUse"><stop stop-color="#98cbff" stop-opacity=".65"/><stop offset="1" stop-color="#c8f8ff" stop-opacity=".85"/></linearGradient>
<linearGradient id="small-left" x1="310" y1="39" x2="334" y2="76" gradientUnits="userSpaceOnUse"><stop stop-color="#a0d0ff"/><stop offset=".65" stop-color="#71bcff"/><stop offset="1" stop-color="#c4efff"/></linearGradient>
<linearGradient id="small-right" x1="333" y1="43" x2="361" y2="64" gradientUnits="userSpaceOnUse"><stop stop-color="#bcf0ff"/><stop offset="1" stop-color="#8ed5f6" stop-opacity=".65"/></linearGradient>
<radialGradient id="planet-base" cx=".45" cy=".46" r=".59"><stop stop-color="#85b6ff"/><stop offset=".58" stop-color="#8ab3ff"/><stop offset=".82" stop-color="#b7d2ff"/><stop offset=".97" stop-color="#e9f3ff"/><stop offset="1" stop-color="white"/></radialGradient>
<radialGradient id="planet-shade" cx=".48" cy=".5" r=".5"><stop stop-color="#7faeff" stop-opacity="0"/><stop offset=".75" stop-color="#598afa" stop-opacity=".12"/><stop offset="1" stop-color="white" stop-opacity=".65"/></radialGradient>
<linearGradient id="ring" x1="480" y1="210" x2="813" y2="165" gradientUnits="userSpaceOnUse"><stop stop-color="#8cbeff" stop-opacity=".65"/><stop offset=".5" stop-color="#d6efff" stop-opacity=".8"/><stop offset="1" stop-color="white" stop-opacity=".95"/></linearGradient>
<filter id="cloud-blur"><feGaussianBlur stdDeviation="10"/></filter>
<filter id="planet-texture"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="3" seed="8"/><feColorMatrix type="matrix" values="0 0 0 0 .35 0 0 0 0 .55 0 0 0 0 1 0 0 0 .23 0"/><feGaussianBlur stdDeviation="2.2"/></filter>
<clipPath id="planet-clip"><ellipse cx="668" cy="185" rx="115" ry="119"/></clipPath>
</defs>
<!-- Soft, translucent architectural ribbons -->
<path d="M0 12L559 241 441 260 0 125Z" fill="url(#beam)"/>
<path d="M156 17L750 251 573 232Z" fill="white" opacity=".25"/>
<path d="M0 126L516 343 569 312 0 126Z" fill="white" opacity=".74"/>
<path d="M0 267L140 208 140 264 0 324Z" fill="#a4caff" opacity=".16"/>
<path d="M171 336L384 246 384 321 239 382Z" fill="#afceff" opacity=".19"/>
<path d="M231 309L384 246" stroke="white" stroke-opacity=".5" stroke-width="2"/>
<path d="M776 291L927 221 1003 246 1003 195 928 169 865 202 865 248Z" fill="#a9cbff" opacity=".39"/>
<path d="M927 169V221" stroke="#f6fcff" stroke-width="1.5" stroke-opacity=".65"/>
<path d="M664 277L934 168 1046 93 989 61 730 244Z" fill="#b7d8ff" opacity=".19"/>
<path d="M0 378L374 223 1055 383 1055 320 392 209Z" fill="white" opacity=".35"/>
<path d="M685 287L930 245 1055 211 919 269 827 304Z" fill="white" opacity=".69"/>
<path d="M713 305L844 286 922 314 805 342Z" fill="#a9caff" opacity=".23"/>
<!-- Floating glass cubes -->
<path d="M96 135L200 88 342 141 235 188Z" fill="url(#cube-top)"/>
<path d="M96 135L235 188 235 308 96 254Z" fill="url(#cube-left)"/>
<path d="M235 188L342 141 342 257 235 308Z" fill="url(#cube-right)"/>
<path d="M96 135L235 188 342 141M235 188V308" stroke="white" stroke-width="1.6" stroke-opacity=".63"/>
<path d="M200 88V148L96 135" fill="#b8c7ff" opacity=".21"/>
<path d="M310 36L332 27 357 37 334 47Z" fill="url(#small-top)"/>
<path d="M310 36L334 47V79L310 69Z" fill="url(#small-left)"/>
<path d="M334 47L357 37V70L334 79Z" fill="url(#small-right)"/>
<path d="M310 36L334 47 357 37M334 47V79" stroke="white" stroke-opacity=".55"/>
<!-- Saturn, with the rear and foreground rings rendered separately -->
<g transform="rotate(-19 663 185)"><ellipse cx="663" cy="185" rx="199" ry="42" stroke="url(#ring)" stroke-width="14"/><ellipse cx="663" cy="183" rx="200" ry="42" stroke="white" stroke-opacity=".77" stroke-width="2"/><ellipse cx="663" cy="185" rx="170" ry="28" stroke="white" stroke-opacity=".85" stroke-width="2"/></g>
<ellipse cx="668" cy="185" rx="115" ry="119" fill="url(#planet-base)"/>
<g clip-path="url(#planet-clip)"><g filter="url(#cloud-blur)"><path d="M563 140L597 89 647 106 635 143 672 157 717 129 747 165 708 193 657 177 614 194 572 171Z" fill="#5f91f2" opacity=".36"/><path d="M574 227L606 197 637 211 670 191 711 220 731 269 700 286 653 248 607 262Z" fill="#689eff" opacity=".54"/><ellipse cx="675" cy="113" rx="51" ry="20" fill="#daeaff" opacity=".49"/><path d="M551 193L579 205 581 235 556 249Z" fill="#477eff" opacity=".6"/><path d="M624 138L643 177 625 193 600 174 604 148Z" fill="#adcfff" opacity=".54"/><path d="M728 197L748 166 769 192 759 245 739 250Z" fill="#9bc8ff" opacity=".6"/></g><rect x="547" y="62" width="241" height="247" filter="url(#planet-texture)" opacity=".6"/><ellipse cx="668" cy="185" rx="115" ry="119" fill="url(#planet-shade)"/></g>
<ellipse cx="668" cy="185" rx="115" ry="119" stroke="white" stroke-opacity=".9" stroke-width="2.5"/>
<g transform="rotate(-19 663 185)"><path d="M862 185A199 42 0 0 1 464 185" stroke="url(#ring)" stroke-width="14"/><path d="M863 183A200 42 0 0 1 463 183" stroke="white" stroke-opacity=".79" stroke-width="2"/><path d="M833 183A170 28 0 0 1 493 183" stroke="white" stroke-opacity=".95" stroke-width="2"/><path d="M862 190A199 42 0 0 1 464 190" stroke="#93c5ff" stroke-opacity=".38" stroke-width="3"/></g>
</svg>
<div class="hero-copy"><h1 id="hero-title">让 <span class="highlight">AI 成为你的超级生产力</span>伙伴</h1><p class="hero-description">整合知识、工具与智能体，完成从思考到执行的全流程任务</p></div>
<div class="features">
<div class="feature"><div class="feature-icon"><svg viewBox="0 0 44 44" fill="none" aria-hidden="true"><path d="M22 3v9" stroke="#0860ff" stroke-width="6" stroke-linecap="round"/><rect x="4" y="12" width="36" height="31" rx="11" fill="#0860ff"/><rect x="0" y="22" width="5" height="10" rx="2" fill="#0860ff"/><rect x="39" y="22" width="5" height="10" rx="2" fill="#0860ff"/><rect x="11" y="22" width="6" height="7" rx="3" fill="white"/><rect x="27" y="22" width="6" height="7" rx="3" fill="white"/><path d="M19 34h7" stroke="white" stroke-width="3" stroke-linecap="round"/></svg></div><div><h2>智能体</h2><p>用自然语言完成复杂任务</p></div></div>
<div class="feature"><div class="feature-icon"><svg viewBox="0 0 44 44" fill="none" aria-hidden="true"><path d="M22 9c-4-5-13-5-17-2v27c5-2 12-2 17 3 5-5 12-5 17-3V7c-4-3-13-3-17 2Z" stroke="#075aff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 9v28" stroke="#075aff" stroke-width="3.6"/></svg></div><div><h2>知识库</h2><p>汇聚企业知识，随时调用</p></div></div>
<div class="feature"><div class="feature-icon"><svg viewBox="0 0 44 44" fill="none" aria-hidden="true"><g stroke="#075aff" stroke-width="3.5"><rect x="6" y="5" width="12" height="12" rx="3.5"/><rect x="25" y="5" width="12" height="12" rx="3.5"/><rect x="6" y="25" width="12" height="12" rx="3.5"/><rect x="25" y="25" width="12" height="12" rx="3.5"/></g></svg></div><div><h2>工具</h2><p>连接丰富工具，提升效率</p></div></div>
</div>
</section><section class="login-card" aria-labelledby="login-title"><div class="login-heading"><h2 id="login-title">欢迎回来</h2><p>登录 agentchat</p></div><form class="login-form" :aria-busy="loading" @submit.prevent="handleLogin"><div class="field"><label for="login-user">用户名</label><div class="input-wrap"><svg class="input-icon" viewBox="0 0 28 28" fill="none" aria-hidden="true"><circle cx="14" cy="8" r="5.4" stroke="currentColor" stroke-width="2"/><path d="M3.5 25v-2c0-4.6 4.6-7.5 10.5-7.5S24.5 18.4 24.5 23v2h-21Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg><input id="login-user" v-model="loginForm.username" type="text" placeholder="请输入用户名" autocomplete="username" required></div></div><div class="field password-field"><label for="login-password">密码</label><div class="input-wrap"><svg class="input-icon" viewBox="0 0 28 28" fill="none" aria-hidden="true"><rect x="3.5" y="11" width="21" height="14" rx="2.5" stroke="currentColor" stroke-width="2"/><path d="M8 11V8a6 6 0 0 1 12 0v3" stroke="currentColor" stroke-width="2"/><circle cx="14" cy="17" r="2" fill="currentColor"/><path d="M14 18v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="login-password" v-model="loginForm.password" :type="showLoginPassword?'text':'password'" placeholder="请输入密码" autocomplete="current-password" required><button class="password-toggle" type="button" :aria-label="showLoginPassword?'隐藏密码':'显示密码'" :aria-pressed="showLoginPassword" aria-controls="login-password" @click="showLoginPassword=!showLoginPassword"><svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M3 14s4-7 11-7 11 7 11 7-4 7-11 7S3 14 3 14Z" stroke="currentColor" stroke-width="1.8"/><circle cx="14" cy="14" r="3.5" stroke="currentColor" stroke-width="1.8"/><path v-if="!showLoginPassword" d="m4 4 20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button></div></div><label class="remember" title="仅记住此电脑上的用户名，不保存密码"><input v-model="rememberUsername" type="checkbox"><span>记住账号</span></label><p v-if="loginError" class="auth-error" role="alert">{{ loginError }}</p><button class="login-button" type="submit" :disabled="loading">{{loading?'登录中…':'登录'}}</button><p class="register">没有账号？<button type="button" @click="goToRegister">立即注册</button></p></form></section></main></div></template>
<style scoped src="./auth-entry.css"></style>
