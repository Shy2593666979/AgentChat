import { onBeforeUnmount, ref } from 'vue';

export function useScrollingScrollbar() {
    const scrolling = ref(false);
    let timer: ReturnType<typeof setTimeout> | undefined;
    function showScrollbar() {
        scrolling.value = true;
        clearTimeout(timer);
        // 停止滚动后短暂保留滚动条，继续滚动时重新计时。
        timer = setTimeout(() => { scrolling.value = false; }, 800);
    }
    onBeforeUnmount(() => clearTimeout(timer));
    return { scrolling, showScrollbar };
}
