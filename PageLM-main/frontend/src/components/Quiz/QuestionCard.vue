<template>
  <div id="quizContent" class="space-y-8">
    <div id="questionCard" class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
      <div class="mb-6">
        <h2 id="questionText" class="mb-4 text-xl font-semibold text-[color:var(--app-text)]">{{ q.question }}</h2>
        <div id="questionImage" :class="q.imageHtml ? '' : 'hidden'" class="mb-4" v-html="q.imageHtml || ''" />
      </div>

      <div id="answerOptions" class="space-y-3">
        <button
          v-for="(opt, i) in q.options"
          :key="i"
          type="button"
          :class="optionClass(i)"
          :aria-pressed="selected === i"
          :disabled="showExp"
          @click="onSelect(i)"
        >
          <div class="flex items-center gap-3 text-left">
            <div
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold transition-all duration-200"
              :class="badgeClass(i)"
            >
              {{ String.fromCharCode(65 + i) }}
            </div>
            <span class="flex-1 text-[color:var(--app-text)]">{{ opt }}</span>
            <svg
              v-if="selected === i && !showExp"
              viewBox="0 0 24 24"
              class="size-5 shrink-0 text-[color:var(--nav-active-border)]"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="m5 13 4 4L19 7" />
            </svg>
          </div>
        </button>
      </div>

      <div class="mt-6 flex flex-col md:flex-row justify-between items-center">
        <button
          type="button"
          @click="onHint"
          class="flex items-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-4 py-2 font-medium text-[color:var(--app-text)] transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)]"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.008m-.008-3.75c0-2.485 2.25-2.25 2.25-5.25a2.25 2.25 0 1 0-4.5 0" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          显示提示
        </button>
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="onSubmit"
            :disabled="selected == null || showExp"
            class="bg-[color:var(--nav-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] text-[color:var(--app-text)] rounded-xl px-5 py-2 font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            提交本题
          </button>
          <button
            type="button"
            @click="onNext"
            :disabled="!showExp"
            class="flex items-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/52 px-6 py-3 font-medium text-[color:var(--app-text)] transition-all duration-300 hover:bg-[color:var(--nav-hover-bg-strong)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ isLast ? '完成测验' : '下一题' }}
            <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </div>
      </div>

      <div v-if="showHint" class="mt-4 rounded-2xl border border-amber-400/60 bg-amber-400/25 p-4 shadow-[0_10px_20px_rgba(251,191,36,0.15)]">
        <p class="text-sm font-semibold text-[color:var(--app-text)]"><strong>提示：</strong>{{ q.hint }}</p>
      </div>

      <div v-if="showExp" class="mt-4 p-5 bg-[color:var(--glass-bg)]/70 border border-[color:var(--glass-border)] rounded-2xl shadow-[0_12px_26px_rgba(15,23,42,0.2)]">
        <h3 class="text-[color:var(--app-text)] font-semibold mb-2">解析</h3>
        <p class="text-[color:var(--nav-text-muted)] text-sm leading-relaxed">{{ q.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Question } from "../../pages/Quiz.vue";

const props = defineProps<{
  q: Question;
  selected: number | null;
  showExp: boolean;
  showHint: boolean;
  onSelect: (i: number) => void;
  onHint: () => void;
  onSubmit: () => void;
  onNext: () => void;
  isLast: boolean;
}>();

const optionClass = (i: number) => {
  const isSel = props.selected === i;
  const isCorrect = props.showExp && i === props.q.correct;
  const isWrongSel = props.showExp && props.selected === i && i !== props.q.correct;
  return [
    "answer-option w-full p-4 border rounded-xl text-left transition-all duration-200 disabled:cursor-not-allowed",
    "border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/28 hover:-translate-y-0.5 hover:border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)]",
    isSel ? "border-[color:var(--nav-active-border)] bg-[color:var(--nav-active-bg)]/90 shadow-[0_10px_24px_rgba(59,130,246,0.18)] ring-2 ring-[color:var(--nav-active-border)]/25" : "",
    isCorrect ? "border-emerald-500/60 bg-emerald-500/15 text-[color:var(--app-text)] ring-2 ring-emerald-500/20" : "",
    isWrongSel ? "border-rose-500/60 bg-rose-500/15 text-[color:var(--app-text)] ring-2 ring-rose-500/20" : "",
  ].join(" ");
};

const badgeClass = (i: number) => {
  const isSel = props.selected === i;
  const isCorrect = props.showExp && i === props.q.correct;
  const isWrongSel = props.showExp && props.selected === i && i !== props.q.correct;

  if (isCorrect) return "border-emerald-500 bg-emerald-500/15 text-emerald-700";
  if (isWrongSel) return "border-rose-500 bg-rose-500/15 text-rose-600";
  if (isSel) return "border-[color:var(--nav-active-border)] bg-[color:var(--nav-active-bg)] text-[color:var(--app-text)]";
  return "border-[color:var(--nav-border)] text-[color:var(--app-text)]";
};
</script>
