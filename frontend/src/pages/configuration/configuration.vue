<template>
 <div class="editor">
  <div ref="editorContainer" class="editor-container"></div>
 </div>
</template>

<script setup lang="ts">
import * as monaco from 'monaco-editor';
import { ref, onMounted} from 'vue';
import { getConfigAPI ,updateConfigAPI} from '../../apis/configuration'



const editorContainer = ref<HTMLElement | null>(null);
let editorInstance: monaco.editor.IStandaloneCodeEditor | null = null;

onMounted(async() => {
  const data = await getConfigAPI()
  if (editorContainer.value) {
    editorInstance = monaco.editor.create(editorContainer.value, {
      value: data.data.data,
      language: 'python',
    });

    editorInstance.onDidChangeModelContent(async() => {
      const value = editorInstance?.getValue();
      const formData = new FormData()
      formData.append("data",String(value))
      await updateConfigAPI(formData)
    });
  }
});


</script>

<style lang="scss" scoped>
.editor {
  display: flex;
  height: calc(100vh - 62px);
  .editor-container{
    margin: 20px;
    width: 100%;
    height: 100%;
    font-size: 20px !important;
  }
}
</style>
