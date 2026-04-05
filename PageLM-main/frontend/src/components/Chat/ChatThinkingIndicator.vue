<template>
  <div
    class="inline-flex max-w-md items-center gap-3 rounded-2xl border border-sky-200/70 bg-white/92 px-4 py-3 shadow-[0_14px_30px_rgba(14,165,233,0.14)] backdrop-blur-md"
    role="status"
    aria-live="polite"
  >
    <span
      class="flex size-10 shrink-0 items-center justify-center rounded-2xl border border-sky-200/80 bg-sky-100/90 text-xl shadow-[0_8px_20px_rgba(56,189,248,0.18)]"
      aria-hidden="true"
    >
      <span class="thinking-emoji">{{ emoji }}</span>
    </span>
    <div class="min-w-0">
      <div class="text-sm font-semibold text-slate-900">{{ title }}</div>
      <div class="mt-0.5 flex items-center gap-2 text-xs leading-5 text-slate-600">
        <span>{{ description }}</span>
        <span class="inline-flex items-center gap-1" aria-hidden="true">
          <span
            v-for="index in 3"
            :key="index"
            class="thinking-dot size-1.5 rounded-full bg-sky-500"
            :style="{ animationDelay: `${index * 0.16}s` }"
          />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  emoji?: string;
  title?: string;
  description?: string;
}>(), {
  emoji: "🤔",
  title: "AI 正在思考回答",
  description: "问题已经收到，正在组织答案",
});
</script>

<style scoped>
.thinking-emoji {
  display: inline-block;
  animation: thinkingFloat 1.7s ease-in-out infinite;
}

.thinking-dot {
  animation: thinkingPulse 0.9s ease-in-out infinite;
}

@keyframes thinkingFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

@keyframes thinkingPulse {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
