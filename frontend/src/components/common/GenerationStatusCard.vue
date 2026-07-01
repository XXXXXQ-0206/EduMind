<template>
  <div
    class="relative overflow-hidden rounded-[28px] border border-white/55 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(247,250,255,0.92))] p-5 shadow-[0_18px_48px_rgba(15,23,42,0.14)] backdrop-blur-xl"
    :class="compact ? 'max-w-xl' : 'w-full max-w-4xl'"
  >
    <div
      class="pointer-events-none absolute inset-0 opacity-70"
      :class="surfaceTone"
      aria-hidden="true"
    />
    <div class="relative">
      <div class="flex items-start gap-4">
        <div
          class="flex size-14 shrink-0 items-center justify-center rounded-[22px] border text-2xl shadow-[0_12px_30px_rgba(15,23,42,0.1)]"
          :class="badgeTone"
        >
          <span class="generation-status-emoji">{{ emoji }}</span>
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <div class="text-base font-semibold text-slate-900">{{ title }}</div>
            <span
              class="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold"
              :class="chipTone"
            >
              <span class="inline-flex size-2 rounded-full bg-current opacity-80 generation-status-ping" />
              {{ currentPhaseLabel }}
            </span>
          </div>
          <p class="mt-1 text-sm leading-6 text-slate-600">{{ description }}</p>
        </div>
      </div>

      <div v-if="steps.length" class="mt-4 grid gap-2 sm:grid-cols-3">
        <div
          v-for="(step, index) in steps"
          :key="step.key"
          class="rounded-2xl border px-3 py-3 transition-all"
          :class="stepTone(stepState(index))"
        >
          <div class="flex items-center gap-2">
            <span
              class="inline-flex size-6 items-center justify-center rounded-full text-[11px] font-semibold"
              :class="stepDotTone(stepState(index))"
            >
              {{ index + 1 }}
            </span>
            <span class="text-sm font-medium text-slate-800">{{ step.label }}</span>
          </div>
          <div class="mt-2 text-xs" :class="stepHintTone(stepState(index))">
            {{ stepState(index) === "done" ? "已完成" : stepState(index) === "current" ? "进行中" : "等待中" }}
          </div>
        </div>
      </div>

      <div class="mt-4 flex items-end gap-2" aria-hidden="true">
        <span
          v-for="index in 4"
          :key="index"
          class="generation-status-bar block w-2 rounded-full"
          :class="barTone"
          :style="{ animationDelay: `${index * 0.12}s` }"
        />
        <span class="ml-2 text-xs font-medium text-slate-500">AI 正在处理，请稍候…</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

type StepItem = { key: string; label: string };
type Tone = "sky" | "violet" | "amber" | "emerald" | "rose";
type StepState = "done" | "current" | "pending";

const props = withDefaults(defineProps<{
  emoji?: string;
  title?: string;
  description?: string;
  phase?: string;
  steps?: StepItem[];
  compact?: boolean;
  tone?: Tone;
}>(), {
  emoji: "⏳",
  title: "AI 正在生成",
  description: "当前任务已经开始处理，结果会在完成后自动显示。",
  phase: "",
  steps: () => [],
  compact: false,
  tone: "sky",
});

const toneMap: Record<Tone, { badge: string; chip: string; surface: string; bar: string }> = {
  sky: {
    badge: "border-sky-200/80 bg-sky-100/90 text-sky-600",
    chip: "border-sky-200/70 bg-sky-50/90 text-sky-700",
    surface: "bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.14),transparent_42%),radial-gradient(circle_at_bottom_left,rgba(125,211,252,0.18),transparent_38%)]",
    bar: "bg-gradient-to-t from-sky-500 to-cyan-300",
  },
  violet: {
    badge: "border-violet-200/80 bg-violet-100/90 text-violet-600",
    chip: "border-violet-200/70 bg-violet-50/90 text-violet-700",
    surface: "bg-[radial-gradient(circle_at_top_right,rgba(167,139,250,0.16),transparent_42%),radial-gradient(circle_at_bottom_left,rgba(216,180,254,0.18),transparent_38%)]",
    bar: "bg-gradient-to-t from-violet-500 to-fuchsia-300",
  },
  amber: {
    badge: "border-amber-200/80 bg-amber-100/90 text-amber-600",
    chip: "border-amber-200/70 bg-amber-50/90 text-amber-700",
    surface: "bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,0.16),transparent_42%),radial-gradient(circle_at_bottom_left,rgba(253,230,138,0.18),transparent_38%)]",
    bar: "bg-gradient-to-t from-amber-500 to-yellow-300",
  },
  emerald: {
    badge: "border-emerald-200/80 bg-emerald-100/90 text-emerald-600",
    chip: "border-emerald-200/70 bg-emerald-50/90 text-emerald-700",
    surface: "bg-[radial-gradient(circle_at_top_right,rgba(52,211,153,0.16),transparent_42%),radial-gradient(circle_at_bottom_left,rgba(110,231,183,0.18),transparent_38%)]",
    bar: "bg-gradient-to-t from-emerald-500 to-lime-300",
  },
  rose: {
    badge: "border-rose-200/80 bg-rose-100/90 text-rose-600",
    chip: "border-rose-200/70 bg-rose-50/90 text-rose-700",
    surface: "bg-[radial-gradient(circle_at_top_right,rgba(251,113,133,0.16),transparent_42%),radial-gradient(circle_at_bottom_left,rgba(253,164,175,0.18),transparent_38%)]",
    bar: "bg-gradient-to-t from-rose-500 to-orange-300",
  },
};

const normalizedPhase = computed(() => (props.phase || "").trim().toLowerCase());
const matchedIndex = computed(() => props.steps.findIndex((step) => step.key.toLowerCase() === normalizedPhase.value));
const currentPhaseLabel = computed(() => {
  if (matchedIndex.value >= 0) return props.steps[matchedIndex.value].label;
  return props.phase?.trim() || "处理中";
});

const badgeTone = computed(() => toneMap[props.tone].badge);
const chipTone = computed(() => toneMap[props.tone].chip);
const surfaceTone = computed(() => toneMap[props.tone].surface);
const barTone = computed(() => toneMap[props.tone].bar);

const stepState = (index: number): StepState => {
  if (!props.steps.length) return "pending";
  if (matchedIndex.value < 0) return index === 0 ? "current" : "pending";
  if (index < matchedIndex.value) return "done";
  if (index === matchedIndex.value) return "current";
  return "pending";
};

const stepTone = (state: StepState) => {
  if (state === "done") return "border-emerald-200/70 bg-emerald-50/70";
  if (state === "current") return "border-slate-200/80 bg-white/95 shadow-[0_10px_25px_rgba(15,23,42,0.08)]";
  return "border-slate-200/70 bg-slate-50/70";
};

const stepDotTone = (state: StepState) => {
  if (state === "done") return "bg-emerald-500 text-white";
  if (state === "current") return "bg-slate-900 text-white";
  return "bg-slate-200 text-slate-500";
};

const stepHintTone = (state: StepState) => {
  if (state === "done") return "text-emerald-600";
  if (state === "current") return "text-slate-700";
  return "text-slate-400";
};
</script>

<style scoped>
.generation-status-emoji {
  animation: generationStatusFloat 1.8s ease-in-out infinite;
  display: inline-block;
}

.generation-status-bar {
  height: 14px;
  animation: generationStatusBar 1.1s ease-in-out infinite;
}

.generation-status-ping {
  animation: generationStatusPing 1.2s ease-in-out infinite;
}

@keyframes generationStatusFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

@keyframes generationStatusBar {
  0%, 100% {
    transform: scaleY(0.45);
    opacity: 0.55;
  }
  50% {
    transform: scaleY(1.4);
    opacity: 1;
  }
}

@keyframes generationStatusPing {
  0%, 100% {
    transform: scale(0.85);
    opacity: 0.45;
  }
  50% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
