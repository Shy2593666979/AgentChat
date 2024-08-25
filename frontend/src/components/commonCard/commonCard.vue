<script lang="ts" setup>

withDefaults(
    defineProps<{
        title: string,
        detail: string,
        type: string,
        imgUrl: string
    }>(),
    {
        title: '预置文本',
        detail: '你好！请问有什么可以帮您的吗我感觉可以帮您可以帮您可以帮您您可以帮您可以帮您',
        type: 'skill',
        imgUrl: 'http://localhost:5173/src/assets/kele.jpg'
    }
)

</script>

<template>
    <div class="historyCard">
        <div class="content">
            <div class="top">
                <img :src=imgUrl alt="" width="40px" height="40px">
                <span>{{ title }}</span>
            </div>
            <div class="middle">
                {{ detail }}
            </div>
        </div>
        <div class="bottom">
            <div class="agent" v-if="type === 'agent'">
                助手
            </div>
            <div class="skill" v-else>
                技能
            </div>
        </div>
    </div>

</template>

<style lang="scss" scoped>
.historyCard {
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
            // overflow: hidden;

            img {
                margin-right: 10px;
            }
        }

        .middle {
            font-size: 14px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 500;
        }
    }

    .bottom {
        display: flex;
        justify-content: end;
        font-size: 13px;
        font-weight: 300;
        color: #f9f9fc;

        .agent {
            padding: 10px;
            background-color: #024de3;
            border-radius: 0 0 10px 0;
        }

        .skill {
            padding: 10px;
            background-color: black;
            border-radius: 0 0 10px 0;
        }
    }
}
</style>