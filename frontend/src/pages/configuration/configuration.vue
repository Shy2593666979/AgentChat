<template>
 <div class="editor">
  <div ref="editorContainer" class="editor-container"></div>
 </div>
</template>

<script setup lang="ts">
import * as monaco from 'monaco-editor';
import { ref, watchEffect, onMounted, defineProps, defineEmits } from 'vue';
import { getConfigAPI } from '../../apis/configuration'
interface Props {
  modelValue: string;
  language: string;
  options: monaco.editor.IStandaloneEditorConstructionOptions;
}

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'javascript'
  },
  options: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['update:modelValue']);

const editorContainer = ref<HTMLElement | null>(null);
let editorInstance: monaco.editor.IStandaloneCodeEditor | null = null;

onMounted(async() => {
  const data = await getConfigAPI()
  if (editorContainer.value) {
    editorInstance = monaco.editor.create(editorContainer.value, {
      value: data.data.data,
      language: props.language,
      ...props.options
    });

    editorInstance.onDidChangeModelContent(() => {
      const value = editorInstance?.getValue();
      emit('update:modelValue', value);
    });
  }
});

watchEffect(() => {
  if (editorInstance) {
    const model = editorInstance.getModel();
    if (model) {
      if (props.modelValue !== model.getValue()) {
        console.log(111)
        model.setValue(props.modelValue);
        console.log(props.modelValue);
      }
    }
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
