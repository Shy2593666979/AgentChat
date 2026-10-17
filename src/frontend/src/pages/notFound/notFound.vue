<script setup lang="ts">
import UserAvatar from "../../components/UserAvatar.vue";
import AppSidebar from '../../components/AppSidebar.vue'
import TopUtility from '../../components/TopUtility.vue'
import UiIcon from '../../components/UiIcon.vue'
import { useUserStore } from '../../store/user'
import { ref, watch } from 'vue'
import {useRouter} from 'vue-router'
const router=useRouter()
const userStore = useUserStore()
const avatarFailed = ref(false)
watch(() => userStore.userInfo?.avatar, () => { avatarFailed.value = false })
const goBack=()=>window.history.length>1?router.back():router.push('/workspace')
</script>
<template><div class="converted-not-found p-shell"><AppSidebar/><main class="error-main">
<header class="topbar"><TopUtility/><router-link class="error-profile" :to="userStore.isLoggedIn ? '/profile' : '/login'" :aria-label="userStore.isLoggedIn ? '个人中心' : '登录'"><span class="avatar"><UserAvatar :username="userStore.userInfo?.username" :src="userStore.userInfo?.avatar"/></span><span v-if="userStore.userInfo?.username" class="profile-name">{{ userStore.userInfo.username }}</span></router-link></header>
<svg class="background-art" viewBox="0 0 1403 470" preserveAspectRatio="none" aria-hidden="true">
<defs>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#b4d8ff" stop-opacity=".18"/><stop offset=".65" stop-color="#ecf9ff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="beamRight" x1="1" y1="0" x2="0" y2="1"><stop stop-color="#bbdbff" stop-opacity=".24"/><stop offset="1" stop-color="#e6f6ff" stop-opacity="0"/></linearGradient>
<linearGradient id="cubeTop" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#b0c4ff" stop-opacity=".64"/><stop offset=".54" stop-color="#bbdeff" stop-opacity=".42"/><stop offset="1" stop-color="#d2ffff" stop-opacity=".72"/></linearGradient>
<linearGradient id="cubeLeft" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c6d9ff" stop-opacity=".7"/><stop offset=".48" stop-color="#a2baff" stop-opacity=".62"/><stop offset="1" stop-color="#edf2ff" stop-opacity=".28"/></linearGradient>
<linearGradient id="cubeRight" x1="1" y1="0" x2="0" y2="1"><stop stop-color="#9ce0ff" stop-opacity=".65"/><stop offset="1" stop-color="#ccddff" stop-opacity=".38"/></linearGradient>
<linearGradient id="smallLeft" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#6ba6fa" stop-opacity=".74"/><stop offset="1" stop-color="#a3eaff" stop-opacity=".65"/></linearGradient>
<linearGradient id="smallRight" x1="1" y1="0" x2="0" y2="1"><stop stop-color="#98bdff" stop-opacity=".6"/><stop offset="1" stop-color="#53c9ff" stop-opacity=".64"/></linearGradient>
<g id="smallCube"><path d="M0 7 18 0 37 8 19 16Z" fill="url(#cubeTop)"/><path d="M0 7v25l19 9V16Z" fill="url(#smallLeft)"/><path d="m19 16 18-8v25l-18 8Z" fill="url(#smallRight)"/><path d="m0 7 19 9L37 8M19 16v25M18 0v16" fill="none" stroke="#f5fbff" stroke-opacity=".7"/></g>
<filter id="soft"><feGaussianBlur stdDeviation="17"/></filter>
</defs>
<ellipse cx="229" cy="161" rx="210" ry="97" fill="#b7ddff" opacity=".24" filter="url(#soft)"/><ellipse cx="1300" cy="185" rx="211" ry="108" fill="#b8d9ff" opacity=".27" filter="url(#soft)"/>
<path d="M0 57 465 339 621 442 0 225Z" fill="url(#beam)" filter="url(#soft)"/><path d="M0 160 533 418 630 449 0 277Z" fill="#fff" opacity=".25"/><path d="M0 246 421 411 612 447 0 334Z" fill="#afd9ff" opacity=".11"/><path d="m25 116 475 262" stroke="#fff" stroke-width="1.6" opacity=".85"/><path d="m24 121 199 99" stroke="#edfbff" stroke-width="5" opacity=".3"/>
<path d="m1403 123-534 294-98 35 632-199Z" fill="url(#beamRight)" filter="url(#soft)"/><path d="m1403 193-465 226-160 35 625-166Z" fill="#fff" opacity=".43"/><path d="m1403 278-507 154-93 23 600-102Z" fill="#a8d5ff" opacity=".13"/><path d="m1269 150-326 231" stroke="#fff" stroke-width="1.4" opacity=".73"/>
<path d="m20 260 66-30 98 39-69 29Z" fill="url(#cubeTop)"/><path d="M20 260v73l95 42v-77Z" fill="url(#cubeLeft)"/><path d="m115 298 69-29v77l-69 29Z" fill="url(#cubeRight)"/><path d="m20 260 95 38 69-29M115 298v77M86 230l98 39" fill="none" stroke="#f8ffff" stroke-width="1.3" opacity=".9"/>
<path d="m115 375 69-29 41 17-110 48Z" fill="#c7eaff" opacity=".23"/><path d="m184 346 41 17v42l-41-18Z" fill="#c1e7ff" opacity=".2"/><path d="m115 375 110-12" stroke="#fff" stroke-opacity=".42"/>
<use href="#smallCube" x="161" y="190"/>
<path d="m1223 262 113-53 64 36-102 49Z" fill="url(#cubeTop)"/><path d="m1223 262 75 32v78l-75-28Z" fill="url(#cubeRight)"/><path d="m1298 294 102-49v79l-102 48Z" fill="url(#cubeLeft)"/><path d="m1223 262 75 32 102-49M1298 294v78M1223 262l113-53" fill="none" stroke="#f6ffff" stroke-width="1.3" opacity=".9"/>
<path d="m1156 354 67-32 75 50-94 55Z" fill="url(#cubeTop)" opacity=".32"/><path d="m1156 354 48 23v50l-48-22Z" fill="#a8d0fa" opacity=".18"/><use href="#smallCube" x="1211" y="189" transform="translate(-121,-19) scale(1.1)"/><use href="#smallCube" x="1049" y="321"/>
<circle cx="913" cy="252" r="1.6" fill="white"/><circle cx="1181" cy="297" r="1.1" fill="white"/>
</svg>
<svg class="planet" viewBox="0 0 470 267" aria-hidden="true">
<defs>
<radialGradient id="orb" cx="55%" cy="53%" r="54%"><stop stop-color="#5495ff"/><stop offset=".5" stop-color="#6ba4ff"/><stop offset=".76" stop-color="#91bcff"/><stop offset=".94" stop-color="#c8e1ff"/><stop offset="1" stop-color="#f6fbff"/></radialGradient>
<radialGradient id="orbShade" cx="50%" cy="48%" r="52%"><stop offset=".59" stop-color="#b3d7ff" stop-opacity="0"/><stop offset=".89" stop-color="#eff8ff" stop-opacity=".15"/><stop offset="1" stop-color="#fff" stop-opacity=".82"/></radialGradient>
<linearGradient id="ring" x1="0" y1="1" x2=".7" y2="0"><stop stop-color="#85b5ff" stop-opacity=".66"/><stop offset=".45" stop-color="#cce7ff" stop-opacity=".6"/><stop offset=".78" stop-color="#f5fcff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity=".95"/></linearGradient>
<linearGradient id="ringFront" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#8fbbff" stop-opacity=".58"/><stop offset=".53" stop-color="#d5eaff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>
<radialGradient id="platform"><stop stop-color="#b3d8ff" stop-opacity=".43"/><stop offset=".68" stop-color="#c7e7ff" stop-opacity=".26"/><stop offset="1" stop-color="#ddecff" stop-opacity=".07"/></radialGradient>
<filter id="cloudBlur"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="orbClouds"><feTurbulence type="fractalNoise" baseFrequency=".021" numOctaves="4" seed="9"/><feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.6 -.63"/><feGaussianBlur stdDeviation="2.4"/></filter>
<filter id="floorBlur"><feGaussianBlur stdDeviation="6"/></filter>
<clipPath id="orbClip"><circle cx="235" cy="115" r="107"/></clipPath>
</defs>
<ellipse cx="235" cy="239" rx="202" ry="28" fill="#c6e2ff" opacity=".17" filter="url(#floorBlur)"/><ellipse cx="235" cy="232" rx="201" ry="29" fill="url(#platform)" stroke="#c6deff" stroke-opacity=".65" stroke-width="2.4"/><path d="M34 231c0-16 90-29 201-29s201 13 201 29" stroke="#fff" stroke-opacity=".94" stroke-width="1.6" fill="none"/><ellipse cx="235" cy="224" rx="149" ry="22" fill="#aed5ff" opacity=".2"/>
<ellipse cx="232" cy="117" rx="188" ry="36" transform="rotate(-17 232 117)" fill="none" stroke="url(#ring)" stroke-width="9"/><ellipse cx="232" cy="117" rx="188" ry="36" transform="rotate(-17 232 117)" fill="none" stroke="#fff" stroke-opacity=".66" stroke-width="1.5"/>
<circle cx="235" cy="115" r="107" fill="url(#orb)"/>
<g clip-path="url(#orbClip)"><path d="M122 44c30-28 53-20 70-5s-1 28 20 32 30-16 42-19 31 15 12 35-44 2-45 22-10 29-32 26-19-32-42-30-34-13-25-61Z" fill="#e7f5ff" opacity=".32" filter="url(#cloudBlur)"/><path d="M295 18c-17 21-38 22-23 44s39 13 44 39-24 23-12 39 41 5 52-15l3-98Z" fill="#ebf7ff" opacity=".45" filter="url(#cloudBlur)"/><path d="M145 146c26-10 24 13 40 29s44 10 45 23-21 27-56 12-55-37-29-64Zm94 18c21-20 49-13 58 3s-17 38-39 40-39-23-19-43Z" fill="#d9efff" opacity=".49" filter="url(#cloudBlur)"/><rect x="123" y="6" width="225" height="218" filter="url(#orbClouds)" opacity=".61"/><ellipse cx="227" cy="109" rx="71" ry="60" fill="#3d88ff" opacity=".15" filter="url(#cloudBlur)"/><circle cx="235" cy="115" r="107" fill="url(#orbShade)"/></g>
<circle cx="235" cy="115" r="107" fill="none" stroke="#fff" stroke-opacity=".77" stroke-width="2.6"/>
<path d="M411.8 62C417.6 81 342 120 242.5 149.8S55.8 188.4 50.2 170" fill="none" stroke="url(#ringFront)" stroke-width="10"/><path d="M411.8 58C417.6 77 342 116 242.5 145.8S55.8 184.4 50.2 166" fill="none" stroke="#f5fcff" stroke-opacity=".94" stroke-width="1.7"/><path d="M374 61c-7-10-31-6-49-3" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.2"/>
</svg>
<section class="error-content" aria-labelledby="error-title"><div class="error-code" aria-label="404">404</div><h1 id="error-title">页面暂时找不到了</h1><p class="description">你访问的页面不存在或已被移动</p><div class="actions"><router-link class="action-button primary" to="/workspace">返回工作台</router-link><button class="action-button secondary" @click="goBack">返回上一页</button></div></section>
</main></div></template>
<style scoped src="./error-page.css"></style>
