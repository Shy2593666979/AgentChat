<script setup lang="ts"></script>

<template>
  <div class="notFound">
    <div>
      <div class="text">抱歉，未找到该页面!</div>
    <div>
      <img src="../../assets/404.gif" alt="" width="500px" height="500px">
    </div>
    </div>
  </div>
</template>

<style>
.notFound{
  height: calc(100vh);
  display: flex;
  justify-content: center;
  align-items: center;
  .text{
    display: flex;
    font-size: 25px;
    justify-content: center;
    color:rgb(157, 157, 157);
  }
}
</style>
