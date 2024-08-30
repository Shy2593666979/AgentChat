import { onMounted } from 'vue';
<script lang="ts" setup>
import { onMounted } from "vue"
import { CardListType } from "../../type"
import {deleteAgentAPI} from '../../apis/history'

const props = defineProps<{
  item: CardListType
}>()

const emits = defineEmits<{
  (event:'delete'):void
}>()

onMounted(() => {
  document.addEventListener('DOMContentLoaded', function() {
  var content = document.getElementById('middle');
  var clampText = function(text: string , maxLines: number) {
    var lines = text.split('\n'); // 按换行符分割文本
    if (lines.length > maxLines) {
      var clampedText = lines.slice(0, maxLines).join('\n') + '...'; // 获取前几行文本并添加省略号
      content.textContent = clampedText; // 设置文本内容
    } else {
      content.textContent = text; // 如果文本行数不超过指定行数，则不添加省略号
    }
  };
  clampText(props.item.description, 3); // 截断为3行
});
})

const  deleteAgent = async() => {
  const formData = new FormData()
  formData.append("id", props.item.id)
  await deleteAgentAPI(formData)
  emits('delete')
}



</script>

<template>
  <div class="agentCard">
    <div class="content">
      <div class="top">
        <img :src="props.item.logo" alt="" width="40px" height="40px" />
        <span>{{ props.item.name }}</span>
      </div>
      <div class="middle" id="middle">
        {{ props.item.description }}
      </div>
      <div class="bottom">
        <div class="delete" @click.stop="deleteAgent">
          <img src="../../assets/delete.svg" width="28px" />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.agentCard {
  margin-top: 10px;
  margin-right: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 150px;
  background-color: #f9f9fc;
  border-radius: 10px;

  .content {
    margin: 5px 0px 0px 10px;

    .top {
      display: flex;
      font-size: 18px;
      align-items: center;
      font-weight: 600;
      margin-bottom: 15px;
      img {
        margin-right: 10px;
      }
    }

    .middle {
      // 只在 WebKit 浏览器中有效
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3; /* 指定显示的行数 */
      overflow: hidden;
      font-size: 14px;
      font-weight: 300;
      height: 55px;
    }
    .bottom {
      margin-top: 5px;
      font-size: 13px;
      font-weight: 300;
      height: 25px;
      display: flex;
      justify-content: end;
      align-items: center;
      .delete {
        display: none;
      }
    }
  }
}
.agentCard:hover {
  background-color: white;
  .delete {
    display: flex !important;
  }
}
</style>
