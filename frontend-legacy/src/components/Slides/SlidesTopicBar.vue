<template>
  <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 mb-8 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)] cursor-pointer"
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
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)] cursor-pointer"
              @click="setInclude(true)"
            >
              是
            </button>
            <button
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)] cursor-pointer"
              @click="setInclude(false)"
            >
              否
            </button>
          </div>
        </div>
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)] cursor-pointer"
            aria-label="生成PPT页数"
            :title="`页数：${pageCount}`"
            @click="toggleCount"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-sky-300 drop-shadow-[0_0_10px_rgba(56,189,248,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 19.5h8M10 16.5v3M14 16.5v3" />
            </svg>
            页数：{{ pageCount }}
          </button>
          <div
            v-if="showCount"
            class="absolute right-0 mt-2 w-24 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button
              v-for="opt in pageCountOptions"
              :key="opt"
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)] cursor-pointer"
              @click="setCount(opt)"
            >
              {{ opt }} 页
            </button>
          </div>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 items-stretch">
        <input
          :value="value"
          @input="onInput"
          :placeholder="placeholder"
          class="flex-1 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-3xl px-5 py-3 text-[color:var(--app-text)] placeholder-stone-500 outline-none"
          aria-label="幻灯片主题"
        />
        <button
          type="button"
          :disabled="disabled"
          @click="onStart"
          class="rounded-full bg-[color:var(--nav-hover-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] duration-300 transition-all text-[color:var(--app-text)] px-5 py-3 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
        >
          <template v-if="isLoading">
            <svg class="size-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" class="opacity-25" />
              <path d="M4 12a8 8 0 0 1 8-8" class="opacity-75" fill="currentColor" />
            </svg>
            正在生成…
          </template>
          <template v-else>
            开始生成
            <svg viewBox="0 0 24 24" class="size-4" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M8 19.5h8M10 16.5v3M14 16.5v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    value: string;
    onChange: (v: string) => void;
    onStart: () => void;
    isLoading?: boolean;
    onSelectInclude?: (include: boolean) => void;
    onSelectPageCount?: (count: number) => void;
    pageCountValue?: number;
    pageCountOptions?: number[];
    materialsLabel?: string;
    placeholder?: string;
  }>(),
  {
    isLoading: false,
    pageCountValue: 10,
    pageCountOptions: () => [10, 15, 20],
    materialsLabel: "备课资料",
    placeholder: "输入主题生成教学幻灯片（例如：牛顿运动定律）",
  }
);

const disabled = computed(() => !props.value.trim() || props.isLoading);

const includeMaterials = ref(false);
const showInclude = ref(false);
const showCount = ref(false);

const pageCount = computed(() => props.pageCountValue ?? 10);
const pageCountOptions = computed(() => props.pageCountOptions ?? [10, 15, 20]);

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
  props.onSelectPageCount?.(next);
};

const onInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  props.onChange(target.value);
};
</script>
