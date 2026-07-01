<template>
  <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 mb-8 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)]"
            :aria-label="materialsLabel"
            :title="includeMaterials ? `${materialsLabel}：是` : `${materialsLabel}：否`"
            @click="toggleInclude"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-amber-300 drop-shadow-[0_0_10px_rgba(251,191,36,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
            </svg>
            <span>{{ materialsLabel }}：{{ includeMaterials ? "是" : "否" }}</span>
          </button>
          <div
            v-if="showInclude"
            class="absolute right-0 mt-2 w-24 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
              @click="setInclude(true)"
            >
              是
            </button>
            <button
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
              @click="setInclude(false)"
            >
              否
            </button>
          </div>
        </div>
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)]"
            aria-label="题目数量"
            :title="`题目数量：${countValue}`"
            @click="toggleCount"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-sky-300 drop-shadow-[0_0_10px_rgba(56,189,248,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7" />
            </svg>
            题目数量：{{ countValue }}
          </button>
          <div
            v-if="showCount"
            class="absolute right-0 mt-2 w-24 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button
              v-for="opt in countOptions"
              :key="opt"
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
              @click="setCount(opt)"
            >
              {{ opt }}
            </button>
          </div>
        </div>
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)]"
            aria-label="选择难度"
            :title="`难度：${difficultyValueLabel}`"
            @click="toggleDifficulty"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-rose-300 drop-shadow-[0_0_10px_rgba(244,63,94,0.5)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75v16.5m7.5-7.5h-15" />
            </svg>
            难度：{{ difficultyValueLabel }}
          </button>
          <div
            v-if="showDifficulty"
            class="absolute right-0 mt-2 w-28 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button
              v-for="opt in difficultyOptions"
              :key="opt.value"
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
              @click="setDifficulty(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 items-stretch">
      <input
        :value="value"
        @input="onInput"
        placeholder="输入主题生成测验（例如：相对论）"
        class="flex-1 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-3xl px-5 py-3 text-[color:var(--app-text)] placeholder-stone-500 outline-none"
      />
      <button
        type="button"
        :disabled="disabled"
        @click="onStart"
        class="rounded-full bg-[color:var(--nav-hover-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] duration-300 transition-all text-[color:var(--app-text)] px-5 py-3 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <template v-if="isLoading">
          <svg class="size-4 animate-spin" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" class="opacity-25" />
            <path d="M4 12a8 8 0 0 1 8-8" class="opacity-75" fill="currentColor" />
          </svg>
          正在生成…
        </template>
        <template v-else>
          开始测验
          <svg viewBox="0 0 24 24" class="size-4" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 12l18-9-6.75 9L21 21 3 12z" fill="currentColor" />
          </svg>
        </template>
      </button>
      </div>
    </div>
    <div v-if="phase" class="text-xs text-stone-500 mt-2">状态: {{ phase }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    value: string;
    onChange: (v: string) => void;
    onStart: () => void;
    phase?: string;
    isLoading?: boolean;
    onSelectInclude?: (include: boolean) => void;
    onSelectCount?: (count: number) => void;
    onSelectDifficulty?: (level: DifficultyLevel) => void;
    countValue?: number;
    countOptions?: number[];
    difficultyValue?: DifficultyLevel;
    materialsLabel?: string;
  }>(),
  { isLoading: false, countValue: 5, countOptions: () => [5, 10, 15], difficultyValue: "medium", materialsLabel: "学习资料" }
);

const disabled = computed(() => !props.value.trim() || props.isLoading);

const includeMaterials = ref(false);
const showInclude = ref(false);
const showCount = ref(false);
const showDifficulty = ref(false);

const toggleInclude = () => {
  showInclude.value = !showInclude.value;
};

const setInclude = (next: boolean) => {
  includeMaterials.value = next;
  showInclude.value = false;
  props.onSelectInclude?.(next);
};

const toggleCount = () => {
  showCount.value = !showCount.value;
};

const setCount = (next: number) => {
  showCount.value = false;
  props.onSelectCount?.(next);
};

const toggleDifficulty = () => {
  showDifficulty.value = !showDifficulty.value;
};

const setDifficulty = (next: DifficultyLevel) => {
  showDifficulty.value = false;
  props.onSelectDifficulty?.(next);
};

const countValue = computed(() => props.countValue || 5);
const countOptions = computed(() => props.countOptions || [5, 10, 15]);

type DifficultyLevel = "easy" | "medium" | "hard";
const difficultyOptions = [
  { value: "easy" as DifficultyLevel, label: "简单" },
  { value: "medium" as DifficultyLevel, label: "中等" },
  { value: "hard" as DifficultyLevel, label: "困难" },
];
const difficultyValueLabel = computed(() => {
  const current = props.difficultyValue || "medium";
  return difficultyOptions.find((o) => o.value === current)?.label || "中等";
});

const onInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  props.onChange(target.value);
};
</script>
