<template>
  <div class="editor">
    <div ref="editorContainer" class="editor-container"></div>
    <div class="button">
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" @click="primary">确定</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as monaco from "monaco-editor"
import { ref, onMounted } from "vue"
import { getConfigAPI, updateConfigAPI } from "../../apis/configuration"

const editorContainer = ref<HTMLElement | null>(null)
let editorInstance: monaco.editor.IStandaloneCodeEditor | null = null
const editorValue = ref("")
onMounted(async () => {
  const data = await getConfigAPI()
  editorValue.value = data.data.data
  if (editorContainer.value) {
    editorInstance = monaco.editor.create(editorContainer.value, {
      value: editorValue.value,
      language: "python",
    })
  }
})

const primary = async () => {
  const value = editorInstance?.getValue()
  const formData = new FormData()
  formData.append("data", String(value))
  const data = await updateConfigAPI(formData)
  if (data.data.data !== "更改配置成功") {
    alert("请检查您输入的信息或者格式是否正确，必须为json格式")
    const data = await getConfigAPI()
    editorInstance?.setValue(data.data.data)
  }else{
    alert("更改配置成功")
  }
}
const cancel = ()=>{
  editorInstance?.setValue(editorValue.value)
}
</script>

<style lang="scss" scoped>
.editor {
  height: calc(100vh - 62px);
  .editor-container {
    margin: 20px;
    width: 100%;
    height: 80%;
    font-size: 20px !important;
  }
  .button {
    display: flex;
    margin-top: 30px;
    justify-content: center;
    :deep(.el-button) {
      padding: 20px 40px;
    }
  }
}
</style>
