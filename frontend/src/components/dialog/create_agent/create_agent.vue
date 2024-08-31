<script lang="ts" setup>
import { ref, onMounted, watch } from "vue"
import { defaultParameterAPI, defaultCodeAPI} from "../../../apis/agent"
import { createAgentAPI, updateAgentAPI } from "../../../apis/history"
import { Plus } from "@element-plus/icons-vue"
import type { UploadProps, UploadUserFile } from "element-plus"
import { CardListType } from "../../../type"

const fileList = ref<UploadUserFile[]>([])
const emits = defineEmits<(event: "update") => void>()
const visible = ref<boolean>(false)
const formRef = ref()
const eventType = ref("")
const id = ref('')
const form = ref({
  avatar: '' ,
  title: "",
  descripte: "",
  parameter: "",
  code: "",
})

const rules = ref({
  avatar: [{ required: true, message: "头像不能为空", trigger: "blur" }],
  title: [{ required: true, message: "标题不能为空", trigger: "blur" }],
  descripte: [{ required: true, message: "描述不能为空", trigger: "blur" }],
})

onMounted(async () => { })

const open = async (event: string, item?: CardListType) => {
  visible.value = true
  eventType.value = event
  fileList.value = []

  if (event === "create") {
    const parameter = await defaultParameterAPI()
    const code = await defaultCodeAPI()
    form.value.parameter = parameter.data.data
    form.value.code = code.data.data
    form.value = {
      avatar: '',
      title: "",
      descripte: "",
      parameter: parameter.data.data,
      code: code.data.data,
    }
  } else {
    if (item) {
      fileList.value.push({
        url: item?.logo,
        name: "default",
      })
      form.value.avatar = item?.logo
      id.value = item.id
      form.value.title = item?.name
      form.value.descripte = item?.description
      form.value.parameter = item?.parameter
      form.value.code = item?.code
    }
  }
}

const close = () => {
  visible.value = false
}
const handleRemove: UploadProps["onRemove"] = (uploadFile, uploadFiles) => {
  (form.value.avatar as unknown as null) = null
}

watch(
  fileList,
  async () => {
    if (fileList.value.length > 1) {   
      form.value.avatar =  fileList.value[0].raw.name
      fileList.value.splice(0, 1);  
    }
    form.value.avatar =  fileList.value[0].raw.name
  },
  { deep: true }
)

const handleConfirm = async () => {
  await formRef.value.validate()
  const formData = new FormData()
  formData.append("name", form.value.title)
  formData.append("description", form.value.descripte)
  formData.append("parameter", form.value.parameter)
  formData.append("code", form.value.code)
  if (eventType.value === "create") {
    formData.append("logoFile", fileList.value[0].raw)
    await createAgentAPI(formData)
  } else {
    formData.append("id", id.value)
    await updateAgentAPI(formData)
  }
  emits("update")
  close()
}

defineExpose({ open, close })
</script>

<template>
  <el-dialog v-model="visible" :width="800" class="know-dialog-layout">
    <template #header>
      <div class="header">
        <h4 class="header-title">
          <span>智能体设置</span>
        </h4>
      </div>
    </template>
    <div class="inner">
      <el-form ref="formRef" :model="form" :rules="rules">
        <el-form-item>
          <el-form-item label="头像" prop="avatar">
            <el-upload v-model:file-list="fileList" action="#" list-type="picture-card" :auto-upload="false"
              :on-remove="handleRemove">
              <el-icon>
                <Plus />
              </el-icon>
            </el-upload>
          </el-form-item>
          <el-form-item label="标题" prop="title" style="margin-left: 20px">
            <el-input v-model="form.title" placeholder="请输入英文或者数字" />
          </el-form-item>
        </el-form-item>
        <el-form-item label="描述" prop="descripte">
          <el-input v-model="form.descripte" :autosize="{ minRows: 4, maxRows: 4 }" type="textarea" placeholder="请输入" />
        </el-form-item>
        <el-form-item label="参数" prop="parameter">
          <el-input v-model="form.parameter" :autosize="{ minRows: 12, maxRows: 12 }" type="textarea"
            placeholder="请输入" />
        </el-form-item>
        <el-form-item label="代码" prop="code">
          <el-input v-model="form.code" :autosize="{ minRows: 12, maxRows: 12 }" type="textarea" placeholder="请输入" />
        </el-form-item>
      </el-form>
    </div>
    <div class="footer">
      <el-button @click="close"> 取消 </el-button>
      <el-button type="primary" @click="handleConfirm"> 确定 </el-button>
    </div>
  </el-dialog>
</template>

<style lang="scss" scoped>
.know-dialog-layout {
  .avatar {
    width: 24px;
    height: 24px;
  }

  .inner {
    :deep(.el-form) {
      padding: 10px;
      display: grid;
      grid-template-columns: 50% 50%;
      gap: 10px;
    }

    :deep(.el-form-item) {
      display: block;
      margin-bottom: 15px !important;
    }

    :deep(.el-textarea__inner) {
      border-radius: 10px;
      resize: none;
      color: #333333;
    }
  }

  .footer {
    margin-top: 24px;
    display: flex;
    justify-content: center;
    padding: 0px 16px;
    margin-bottom: 24px;

    .public-button.el-button:not(.is-link) {
      border: 1px solid rgb(173, 176, 184);
      font-size: 14px;
      font-weight: 400;
    }
  }
}

.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.el-icon.avatar-uploader-icon {
  border: 1px solid #e2e4e8;
  border-radius: 4px;
  font-size: 28px;
  color: #8c939d;
  width: 60px;
  height: 60px;
  text-align: center;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 60px;
  height: 60px;
}

:deep(.el-upload--picture-card) {
  width: 60px;
  height: 60px;
}

:deep(.el-upload-list--picture-card .el-upload-list__item-actions span.el-upload-list__item-preview) {
  display: none;
}

:deep(.el-icon) {
  margin: 0 !important;
}

:deep(.el-upload-list--picture-card .el-upload-list__item-actions span + span) {
  margin: 0 !important;
}
</style>
