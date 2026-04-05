<template>
  <div id="resultsScreen" class="text-center space-y-6">
    <div class="bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] rounded-3xl p-8 shadow-[0_18px_40px_rgba(15,23,42,0.25)]">
      <div id="resultIcon" class="text-6xl mb-4 flex justify-center">
        <component :is="iconComponent" class="size-12 text-sky-300" />
      </div>
      <h2 class="mb-2 text-3xl font-bold text-[color:var(--app-text)]">测验完成!</h2>
      <p class="text-xl text-[color:var(--nav-text)] mb-6">
        你的得分：<span id="finalScore" class="text-sky-300 font-bold">{{ score }}/{{ total }} ({{ percentage }}%)</span>
      </p>

      <div id="resultMessage" :class="['mb-6 p-5 rounded-2xl border shadow-[0_12px_24px_rgba(0,0,0,0.2)]', visual.cls]">
        <p class="text-lg font-bold text-[color:var(--app-text)]">{{ visual.msg }}</p>
      </div>

      <div class="mb-6 text-left">
        <h3 class="mb-3 font-semibold text-[color:var(--app-text)]">表现统计:</h3>
        <div id="performanceStats" class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          <div class="flex items-center justify-between rounded-2xl border border-green-500/30 bg-green-500/10 px-4 py-3">
            <span class="flex items-center gap-2">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4 text-green-400">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
              </svg>
              正确答案:
            </span>
            <span class="text-green-300 text-lg font-semibold">{{ correct }}</span>
          </div>

          <div class="flex items-center justify-between rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3">
            <span class="flex items-center gap-2">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4 text-red-400">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
              </svg>
              错误答案:
            </span>
            <span class="text-red-300 text-lg font-semibold">{{ answers.length - correct }}</span>
          </div>

          <div class="flex items-center justify-between rounded-2xl border border-sky-500/30 bg-sky-500/10 px-4 py-3">
            <span class="flex items-center gap-2">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4 text-sky-400">
                <path stroke-linecap="round" stroke-linejoin="round" d="m8.99 14.993 6-6m6 3.001c0 1.268-.63 2.39-1.593 3.069a3.746 3.746 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043 3.745 3.745 0 0 1-3.068 1.593c-1.268 0-2.39-.63-3.068-1.593a3.745 3.745 0 0 1-3.296-1.043 3.746 3.746 0 0 1-1.043-3.297 3.746 3.746 0 0 1-1.593-3.068c0-1.268.63-2.39 1.593-3.068a3.746 3.746 0 0 1 1.043-3.297 3.745 3.745 0 0 1 3.296-1.042 3.745 3.745 0 0 1 3.068-1.594c1.268 0 2.39.63 3.068 1.593a3.745 3.745 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.297 3.746 3.746 0 0 1 1.593 3.068ZM9.74 9.743h.008v.007H9.74v-.007Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm4.125 4.5h.008v.008h-.008v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
              准确率:
            </span>
            <span class="text-sky-300 text-lg font-semibold">{{ percentage }}%</span>
          </div>
        </div>
      </div>

      <div class="mb-6 text-left">
        <h3 class="mb-3 font-semibold text-[color:var(--app-text)]">题目结果:</h3>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="(a, i) in answers"
            :key="`${a.questionId}-${i}`"
            type="button"
            class="size-9 rounded-full flex items-center justify-center border text-xs font-semibold transition-colors"
            :class="a.correct ? 'bg-green-500/15 border-green-500/40 text-[color:var(--app-text)]' : 'bg-red-500/15 border-red-500/40 text-[color:var(--app-text)]'"
            :title="a.correct ? '答对' : '答错'"
            @click="onReviewQuestion?.(i)"
          >
            {{ i + 1 }}
          </button>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-4 justify-center mt-2">
        <button
          type="button"
          @click="onRetake"
          class="flex items-center justify-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-6 py-3 font-medium text-[color:var(--app-text)] transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)]"
        >
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          重做测验
        </button>

        <button
          type="button"
          @click="onReview"
          class="flex items-center justify-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-6 py-3 font-medium text-[color:var(--app-text)] transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)]"
        >
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178-.07.207-.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
          查看答案
        </button>

        <button
          type="button"
          @click="onNewTopic"
          class="flex items-center justify-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-6 py-3 font-medium text-[color:var(--app-text)] transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)]"
        >
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75a8.987 8.987 0 0 0-3 .512v14.25A8.987 8.987 0 0 0 6 18a8.967 8.967 0 0 1 6 2.292m0-14.25A8.966 8.966 0 0 1 18 3.75a8.987 8.987 0 0 1 3 .512v14.25A8.987 8.987 0 0 1 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
          </svg>
          新主题
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { UA } from "../../pages/Quiz.vue";

const props = defineProps<{
  score: number;
  total: number;
  percentage: number;
  visual: { msg: string; cls: string; icon: "trophy" | "spark" | "book" | "bolt" };
  answers: UA[];
  onRetake: () => void;
  onReview: () => void;
  onNewTopic: () => void;
  onReviewQuestion?: (index: number) => void;
}>();

const correct = computed(() => props.answers.filter((a) => a.correct).length);

const iconComponent = computed(() => {
  switch (props.visual.icon) {
    case "trophy":
      return {
        template: `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 5h8v3a4 4 0 0 1-8 0V5Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 5H4a2 2 0 0 0 2 2m12-2h2a2 2 0 0 1-2 2" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 12v4m-4 3h8" />
          </svg>
        `,
      };
    case "spark":
      return {
        template: `
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 4.5a.75.75 0 0 1 .721.544l.813 2.846a3.75 3.75 0 0 0 2.576 2.576l2.846.813a.75.75 0 0 1 0 1.442l-2.846.813a3.75 3.75 0 0 0-2.576 2.576l-.813 2.846a.75.75 0 0 1-1.442 0l-.813-2.846a3.75 3.75 0 0 0-2.576-2.576l-2.846-.813a.75.75 0 0 1 0-1.442l2.846-.813A3.75 3.75 0 0 0 7.466 7.89l.813-2.846A.75.75 0 0 1 9 4.5Z" />
          </svg>
        `,
      };
    case "book":
      return {
        template: `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75A2.25 2.25 0 0 1 6.75 4.5h10.5A2.25 2.25 0 0 1 19.5 6.75v10.5A2.25 2.25 0 0 1 17.25 19.5H6.75A2.25 2.25 0 0 1 4.5 17.25Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 8.25h6M9 12h6M9 15.75h4.5" />
          </svg>
        `,
      };
    default:
      return {
        template: `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V4.5a.75.75 0 0 0-1.5 0V10H7a.75.75 0 0 0-.53 1.28l5 5a.75.75 0 0 0 1.06 0l5-5A.75.75 0 0 0 17 10h-4Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 19.5h14" />
          </svg>
        `,
      };
  }
});
</script>
