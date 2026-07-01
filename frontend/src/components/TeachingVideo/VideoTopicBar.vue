<template>
  <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 mb-8 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2"
            :aria-label="materialsLabel"
            :title="includeMaterials ? `${materialsLabel}：是` : `${materialsLabel}：否`"
            @click="toggleInclude"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-amber-300" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
            </svg>
            <span>{{ materialsLabel }}：{{ includeMaterials ? "是" : "否" }}</span>
          </button>
          <div
            v-if="showInclude"
            class="absolute right-0 mt-2 w-24 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button type="button" class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]" @click="setInclude(true)">是</button>
            <button type="button" class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]" @click="setInclude(false)">否</button>
          </div>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 items-stretch">
        <input
          :value="value"
          @input="onInput"
          placeholder="输入主题生成教学视频（例如：牛顿第一定律）"
          class="flex-1 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-3xl px-5 py-3 text-[color:var(--app-text)] placeholder-stone-500 outline-none"
        />
        <button
          type="button"
          :disabled="disabled"
          @click="onStart()"
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
            生成教学视频
            <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
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
    /** 点击生成时传入当前输入的主题，避免父组件 topic 未同步导致第一次点击无效 */
    onStart: (topic: string) => void;
    isLoading?: boolean;
    onSelectInclude?: (include: boolean) => void;
    materialsLabel?: string;
  }>(),
  { isLoading: false, materialsLabel: "备课资料" }
);

const disabled = computed(() => !props.value.trim() || props.isLoading);

const onStart = () => {
  const t = props.value.trim();
  if (t) props.onStart(t);
};

const includeMaterials = ref(false);
const showInclude = ref(false);

const toggleInclude = () => {
  showInclude.value = !showInclude.value;
};

const setInclude = (next: boolean) => {
  includeMaterials.value = next;
  showInclude.value = false;
  props.onSelectInclude?.(next);
};

const onInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  props.onChange(target.value);
};
</script>
