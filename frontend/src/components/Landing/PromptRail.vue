<template>
  <div class="items-center justify-center pt-2 mt-2 md:mt-0 hidden md:flex">
    <div class="relative z-0 rounded-3xl rounded-tl-[22px] rounded-bl-2xl md:rounded-r-none h-full p-2 px-4 border border-stone-800 md:border-r-0 text-sm flex items-center -ml-4 md:-ml-6.5 overflow-hidden max-w-sm">
      <div ref="railRef" class="h-8 overflow-hidden relative w-full cursor-grab active:cursor-grabbing">
        <div class="transition-transform duration-500 ease-in-out" :style="{ transform: `translateY(${translateY}px)` }">
          <div v-for="(prompt, i) in prompts" :key="i" class="h-8 flex items-center">
            <span class="text-sm md:text-xs">{{ prompt }}</span>
          </div>
        </div>
      </div>
    </div>

    <button
      type="button"
      @click="sendNow"
      :disabled="busy"
      class="h-full w-fit px-3 flex items-center justify-center bg-stone-900/50 border border-stone-900 border-l-0 rounded-r-2xl relative z-10 pointer-events-auto"
      aria-label="发送建议的提示"
      :title="busy ? '开始中...' : '发送'"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="size-5" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { chatJSON } from "../../lib/api";

const props = defineProps<{ onSend?: (prompt: string) => void }>();

const prompts = [
  "教我二次方程课。假设我完全不知道。",
  "解释光合作用的基础。",
  "我如何写一个引人入胜的短篇故事？",
  "什么是机器学习，它如何工作？",
  "教我烹饪的基础知识。",
  "帮助我理解法国大革命。",
  "解释编程概念。",
  "我如何管理个人财务？",
];

const ITEM_H = 32;

const railRef = ref<HTMLDivElement | null>(null);
const index = ref(2);
const busy = ref(false);
const reducedMotion = ref(false);
const router = useRouter();

const translateY = computed(() => -(index.value * ITEM_H));

const updateReducedMotion = () => {
  const m = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  reducedMotion.value = !!m?.matches;
};

let timer: number | undefined;

let removeListeners: (() => void) | null = null;

onMounted(() => {
  updateReducedMotion();
  const m = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  const on = () => updateReducedMotion();
  m?.addEventListener?.("change", on);

  if (!reducedMotion.value) {
    timer = window.setInterval(() => {
      index.value = (index.value + 1) % prompts.length;
    }, 3500);
  }

  const el = railRef.value;
  if (!el) return;

  let dragging = false;
  let startY = 0;
  let startIndex = 0;

  const down = (e: PointerEvent) => {
    dragging = true;
    startY = e.clientY;
    startIndex = index.value;
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };
  const move = (e: PointerEvent) => {
    if (!dragging) return;
    const delta = Math.round(-(e.clientY - startY) / ITEM_H);
    const next = Math.max(0, Math.min(prompts.length - 1, startIndex + delta));
    if (next !== index.value) index.value = next;
  };
  const up = (e: PointerEvent) => {
    dragging = false;
    (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
  };

  el.addEventListener("pointerdown", down, { passive: true });
  window.addEventListener("pointermove", move, { passive: true });
  window.addEventListener("pointerup", up, { passive: true });

  removeListeners = () => {
    if (timer) window.clearInterval(timer);
    el.removeEventListener("pointerdown", down);
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    m?.removeEventListener?.("change", on);
  };
});

onBeforeUnmount(() => {
  removeListeners?.();
});

const sendNow = async () => {
  const q = prompts[index.value];
  if (busy.value) return;
  if (props.onSend) {
    props.onSend(q);
    return;
  }
  try {
    busy.value = true;
    const r = await chatJSON({ q });
    const cid = r?.chatId || "";
    router.push({
      path: "/chat",
      query: { chatId: cid, q },
      state: { chatId: cid, q },
    });
  } finally {
    busy.value = false;
  }
};
</script>
