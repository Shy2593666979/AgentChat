<script setup lang="ts">
import { reactive, ref } from 'vue'
import CommonCard from '../../components/commonCard';

const emits = defineEmits<{
   (event: 'goChat',title:string): void;
}>();

const drawer = ref(false)
const cardList = reactive([
    {
        id:'11111111',
        title:'你好1'
    },
    {
        id:'2',
        title:'你好2'
    },
    {
        id:'3',
        title:'你好3'
    },
    {
        id:'4',
        title:'你好4'
    },
    {
        id:'5',
        title:'你好5'
    },
    {
        id:'6',
        title:'你好6'
    }
])
const currentId = ref(cardList[0].id)
const curentItem = ref(cardList[0])

const open = () => {
    drawer.value = true
}
const close = () => {
    drawer.value = false
}
const optionCard =(item:any) =>{
    currentId.value = item.id
    curentItem.value = item
}
const cancel = ()=>{
    close()
}
const primary = ()=>{
    emits('goChat',curentItem.value.title)
    close()
}

defineExpose({
    open,
    close,
})
</script>

<template>
    <div class="drawer">
        <el-drawer v-model="drawer" title="请选择一个应用" :with-header="true">
            <div class="card">
                <div v-for="item in cardList" :class="currentId === item.id ? 'active':''">
                    <CommonCard @click="optionCard(item)"></CommonCard>
                </div>
            </div>
            <div class="button">
                <el-button @click="cancel">取消</el-button>
                <el-button type="primary" @click="primary">确定</el-button>
            </div>
        </el-drawer>
    </div>
</template>

<style lang="scss" scoped>
.drawer {
    .card {
        display: grid;
        grid-template-columns: 100%;
        gap: 10px;
    }
    .button{
        display: flex;
        margin-top: 15px;
        justify-content: center;
        :deep(.el-button){
            padding: 20px 40px;
        }
    }
    .active{
        border: 1px solid blue;
        border-radius: 4px 4px 10px 4px;
    }
}
</style>