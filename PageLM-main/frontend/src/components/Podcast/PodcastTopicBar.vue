<template>
  <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_12px_20px_rgba(0,0,0,0.2)]"
            aria-label="学习资料"
            :title="includeMaterials ? '学习资料：是' : '学习资料：否'"
            @click="toggleInclude"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-amber-300 drop-shadow-[0_0_10px_rgba(251,191,36,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
            </svg>
            <span>学习资料：{{ includeMaterials ? "是" : "否" }}</span>
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
            aria-label="音频长度"
            :title="`音频长度：${lengthValueLabel}`"
            @click="toggleLength"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-sky-300 drop-shadow-[0_0_10px_rgba(56,189,248,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
              <circle cx="12" cy="12" r="9" />
            </svg>
            音频长度：{{ lengthValueLabel }}
          </button>
          <div
            v-if="showLength"
            class="absolute right-0 mt-2 w-28 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
            <button
              v-for="opt in lengthOptions"
              :key="opt.value"
              type="button"
              class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
              @click="setLength(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- 学习资料模式提示 -->
      <div v-if="includeMaterials" class="flex items-center gap-2 px-1">
        <span class="inline-block size-2 rounded-full bg-amber-400 animate-pulse" />
        <span class="text-xs text-amber-400/90">已启用学习资料模式 — 播客内容将基于您的学习资料生成，可选填补充主题</span>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 items-stretch">
        <input
          :value="value"
          @input="onInput"
          :placeholder="includeMaterials ? '已选择学习资料，可直接生成或输入补充主题' : '输入主题生成播客（例如：通信协议）'"
          class="flex-1 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-3xl px-5 py-3 text-[color:var(--app-text)] placeholder-stone-500 outline-none"
          @keydown.enter.exact.prevent="!disabled && onStart()"
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
            生成中…
          </template>
          <template v-else>
            生成播客
            <svg viewBox="0 0 24 24" class="size-4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 12l18-9-6.75 9L21 21 3 12z" fill="currentColor" />
            </svg>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

type LengthValue = "short" | "medium" | "long";

const props = withDefaults(
  defineProps<{
    value: string;
    onChange: (v: string) => void;
    onStart: () => void;
    isLoading?: boolean;
    onSelectInclude?: (include: boolean) => void;
    onSelectLength?: (length: LengthValue) => void;
    lengthValue?: LengthValue;
  }>(),
  { isLoading: false, lengthValue: "medium" }
);

const disabled = computed(() => {
  // 选择了学习资料时，允许不输入主题
  if (includeMaterials.value) return props.isLoading;
  return !props.value.trim() || props.isLoading;
});

const includeMaterials = ref(false);
const showInclude = ref(false);
const showLength = ref(false);

const toggleInclude = () => {
  showInclude.value = !showInclude.value;
};

const setInclude = (next: boolean) => {
  includeMaterials.value = next;
  showInclude.value = false;
  props.onSelectInclude?.(next);
};

const toggleLength = () => {
  showLength.value = !showLength.value;
};

const setLength = (next: LengthValue) => {
  showLength.value = false;
  props.onSelectLength?.(next);
};

const lengthOptions = [
  { value: "short" as LengthValue, label: "短" },
  { value: "medium" as LengthValue, label: "中" },
  { value: "long" as LengthValue, label: "长" },
];

const lengthValueLabel = computed(() => {
  const current = props.lengthValue || "medium";
  return lengthOptions.find((o) => o.value === current)?.label || "中";
});

const onInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  props.onChange(target.value);
};
</script>
