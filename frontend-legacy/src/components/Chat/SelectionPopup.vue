<template>
  <div
    v-if="selected"
    :ref="popupRef"
    class="absolute z-50 rounded-2xl bg-[color:var(--glass-bg)]/90 border border-[color:var(--glass-border)] p-2.5 shadow-[0_18px_35px_rgba(15,23,42,0.18)] backdrop-blur-md"
    :style="{ left: `${selected.x}px`, top: `${selected.y + 10}px`, transition: 'opacity .15s' }"
  >
    <button
      type="button"
      @click="addNote(selected.text)"
      class="bg-[color:var(--nav-hover-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] border border-transparent text-[color:var(--app-text)] px-3 py-1.5 rounded-xl text-xs transition-all duration-200 active:scale-95 mr-1 inline-flex items-center gap-1.5 cursor-pointer"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 3.487a2.25 2.25 0 0 1 3.182 3.182L7.5 19.213 3 21l1.787-4.5L16.862 3.487Z" />
      </svg>
      添加笔记
    </button>
    <button
      type="button"
      @click="askDoubt(selected.text)"
      class="bg-[color:var(--nav-hover-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] border border-transparent text-[color:var(--app-text)] px-3 py-1.5 rounded-xl text-xs transition-all duration-200 active:scale-95 ml-1 inline-flex items-center gap-1.5 cursor-pointer"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.008m0-3.75c0-2.485 2.25-2.25 2.25-5.25a2.25 2.25 0 1 0-4.5 0" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
      提问
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Ref } from "vue";

defineProps<{
  selected: { text: string; x: number; y: number } | null;
  addNote: (text: string) => void;
  askDoubt: (text: string) => void;
  popupRef: Ref<HTMLDivElement | null>;
}>();
</script>
