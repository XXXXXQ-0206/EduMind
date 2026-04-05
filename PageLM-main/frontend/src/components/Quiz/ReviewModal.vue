<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
    <div class="w-full max-w-2xl rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] p-6 shadow-[0_22px_48px_rgba(15,23,42,0.24)]">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-[color:var(--app-text)]">查看答案</h2>
        <button type="button" @click="onClose" class="rounded-xl p-2 transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)]" aria-label="关闭">
          <svg class="size-6 text-[color:var(--nav-text-muted)] hover:text-[color:var(--app-text)]" fill="none" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="np-scroll space-y-6 max-h-[60vh] overflow-y-auto pr-1">
        <div
          v-for="(a, i) in answers"
          :key="i"
          :id="`review-q-${i}`"
          class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/42 p-4"
        >
          <div class="flex items-start gap-3 mb-3">
            <svg
              v-if="a.correct"
              viewBox="0 0 24 24"
              class="size-6 text-green-400 flex-shrink-0"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75S21.75 6.615 21.75 12 17.385 21.75 12 21.75 2.25 17.385 2.25 12Zm13.36-2.31a.75.75 0 1 0-1.22-.9l-3.41 4.62-1.62-1.62a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.16-.09l3.9-5.28Z"
                clip-rule="evenodd"
              />
            </svg>
            <svg
              v-else
              class="size-6 text-red-400 flex-shrink-0"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm3.53 6.72a.75.75 0 0 0-1.06-1.06L12 10.38 9.53 7.91a.75.75 0 0 0-1.06 1.06L10.94 11.5l-2.47 2.47a.75.75 0 1 0 1.06 1.06L12 12.56l2.47 2.47a.75.75 0 1 0 1.06-1.06L13.06 11.5l2.47-2.53Z"
                clip-rule="evenodd"
              />
            </svg>
            <div class="flex-1">
              <h3 class="mb-2 font-medium text-[color:var(--app-text)]">问题 {{ i + 1 }}</h3>
              <p class="mb-3 text-sm text-[color:var(--nav-text)]">{{ a.question }}</p>
              <div class="space-y-1 text-sm">
                <p :class="a.correct ? 'text-green-400' : 'text-red-400'">你的答案: {{ a.selectedOption }}</p>
                <p v-if="!a.correct" class="text-green-400">正确答案: {{ a.correctOption }}</p>
                <p v-if="a.explanation" class="text-[color:var(--nav-text-muted)]">解释: {{ a.explanation }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!answers.length" class="text-[color:var(--nav-text-muted)]">暂无答案。</div>
      </div>

      <div class="mt-6 flex justify-end">
        <button type="button" @click="onClose" class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-5 py-2 text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]">
          关闭
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import type { UA } from "../../pages/Quiz.vue";

import { nextTick, onMounted, watch } from "vue";

const props = defineProps<{ answers: UA[]; onClose: () => void; initialIndex?: number | null }>();

const scrollToIndex = async (index?: number | null) => {
  if (index == null || index < 0) return;
  await nextTick();
  const el = document.getElementById(`review-q-${index}`);
  el?.scrollIntoView({ behavior: "smooth", block: "center" });
};

onMounted(() => {
  scrollToIndex(props.initialIndex);
});

watch(
  () => props.initialIndex,
  (next) => {
    scrollToIndex(next ?? null);
  }
);
</script>

<style>
.np-scroll::-webkit-scrollbar { width: 10px; height: 10px; }
.np-scroll::-webkit-scrollbar-track { background: color-mix(in srgb, var(--nav-bg) 70%, transparent); border-radius: 9999px; }
.np-scroll::-webkit-scrollbar-thumb { background: color-mix(in srgb, var(--nav-border) 84%, var(--nav-text-muted)); border-radius: 9999px; border: 2px solid color-mix(in srgb, var(--nav-bg) 70%, transparent); }
.np-scroll::-webkit-scrollbar-thumb:hover { background: color-mix(in srgb, var(--nav-border) 72%, var(--app-text)); }
.np-scroll { scrollbar-width: thin; scrollbar-color: color-mix(in srgb, var(--nav-border) 84%, var(--nav-text-muted)) color-mix(in srgb, var(--nav-bg) 70%, transparent); }
</style>
