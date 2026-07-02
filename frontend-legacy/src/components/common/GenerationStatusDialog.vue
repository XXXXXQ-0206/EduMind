<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[95] flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      aria-live="polite"
    >
      <div class="absolute inset-0 bg-slate-950/36 backdrop-blur-[6px]" aria-hidden="true" />
      <div class="relative w-full max-w-2xl animate-[fadeIn_180ms_ease-out]">
        <GenerationStatusCard
          :emoji="emoji"
          :tone="tone"
          :title="title"
          :description="description"
          :phase="phase"
          :steps="steps"
        />
        <p class="mt-3 text-center text-xs font-medium tracking-[0.08em] text-white/88">
          生成完成后会自动展示结果
        </p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import GenerationStatusCard from "./GenerationStatusCard.vue";

type StepItem = { key: string; label: string };
type Tone = "sky" | "violet" | "amber" | "emerald" | "rose";

withDefaults(defineProps<{
  open: boolean;
  emoji?: string;
  title?: string;
  description?: string;
  phase?: string;
  steps?: StepItem[];
  tone?: Tone;
}>(), {
  emoji: "⏳",
  title: "AI 正在生成",
  description: "当前任务已经开始处理，结果会在完成后自动显示。",
  phase: "",
  steps: () => [],
  tone: "sky",
});
</script>
