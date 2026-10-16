<script setup lang="ts">
import BrandLogo from './BrandLogo.vue'
import UiIcon from './UiIcon.vue'
</script>
<template>
  <section class="p-auth-story">
    <BrandLogo />
    <span class="p-eyebrow">A QUIETER SPACE FOR BIGGER IDEAS.</span>
    <h2>让复杂，变清晰。<br />让想法，有回响。</h2>
    <p>连接模型、工具与知识，<br />在一个舒适的空间里，把事情慢慢做好。</p>
    <div class="p-auth-illustration" aria-hidden="true">
      <div class="p-orbit"></div><div class="p-auth-core"><BrandLogo compact /></div>
      <div class="p-floating-label p-label-knowledge"><UiIcon name="book" />你的知识</div>
      <div class="p-floating-label p-label-idea"><UiIcon name="spark" />你的想法</div>
      <div class="p-floating-label p-label-agent"><UiIcon name="bot" />你的智能体</div>
    </div>
    <div class="p-auth-quote">“好的工具，让你专注于真正重要的事情。”<small>agentchat · 个人与团队的智能工作空间</small></div>
  </section>
</template>
