<template>
  <div id="quizHeader" class="text-center mb-8">
    <h1 class="text-3xl font-bold text-[color:var(--app-text)] mb-2">{{ topic }}</h1>
    <p class="text-[color:var(--nav-text-muted)]">用 {{ total }} 道题检验你的掌握情况</p>
    <div class="mt-4 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl px-5 py-3 inline-block">
      <div class="flex items-center gap-4 text-sm">
        <span class="text-[color:var(--nav-text)]">第 <span id="currentQuestion">{{ Math.min(idx + 1, total) }}</span> / <span id="totalQuestions">{{ total }}</span> 题</span>
        <div class="w-48 bg-[color:var(--app-bg-2)] rounded-full h-2">
          <div id="progressBar" class="bg-[color:var(--primary-blue)] h-2 rounded-full transition-all duration-300" :style="{ width: `${pct}%` }" />
        </div>
        <span class="text-[color:var(--nav-text)]">得分：<span id="currentScore">{{ score }}</span></span>
      </div>
    </div>
    <div v-if="total" class="mt-4 flex flex-wrap justify-center gap-2">
      <button
        v-for="n in total"
        :key="n"
        type="button"
        class="size-9 rounded-full border text-xs font-semibold transition-colors"
        :class="[
          idx + 1 === n
            ? 'bg-[color:var(--nav-active-bg)] border-[color:var(--nav-active-border)] text-[color:var(--app-text)]'
            : status?.[n - 1] === 'correct'
              ? 'bg-emerald-500/15 border-emerald-500/40 text-[color:var(--app-text)]'
              : status?.[n - 1] === 'wrong'
                ? 'bg-rose-500/15 border-rose-500/40 text-[color:var(--app-text)]'
                : 'bg-transparent border-slate-500/50 text-slate-400'
        ]"
        @click="onJump?.(n - 1)"
      >
        {{ n }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  topic: string;
  idx: number;
  total: number;
  score: number;
  status?: Array<"correct" | "wrong" | "unanswered">;
  onJump?: (index: number) => void;
}>();
const pct = computed(() => Math.round(((props.idx + 1) / props.total) * 100));
</script>
