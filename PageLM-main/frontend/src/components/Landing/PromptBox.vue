<template>
  <div class="relative rounded-3xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-[0_16px_36px_rgba(15,23,42,0.12),0_1px_0_rgba(255,255,255,0.55)]">
    <span class="ai-spark ai-spark--left" aria-hidden="true"></span>
    <div class="p-3">
      <textarea
        rows="1"
        placeholder="教我任何东西..."
        class="w-full text-[color:var(--app-text)] bg-transparent rounded-2xl p-2.5 outline-none resize-none leading-6 min-h-[40px]"
        :value="value"
        @input="onInput"
        @keydown.enter.exact.prevent="onSend"
        aria-label="主要提示"
      ></textarea>
    </div>

    <div class="px-3 pb-3 flex items-center justify-end gap-3">
      <div class="relative">
        <button
          type="button"
          class="rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] duration-200 transition-colors px-3 py-2 text-xs text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_10px_18px_rgba(0,0,0,0.12)]"
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
          class="rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] duration-200 transition-colors px-3 py-2 text-xs text-[color:var(--app-text)] inline-flex items-center gap-2 shadow-[0_10px_18px_rgba(0,0,0,0.12)]"
          aria-label="选择回复长度"
          :title="responseLengthText ? `回复长度：${responseLengthText}` : '选择回复长度'"
          @click="onToggleLength"
        >
          <svg viewBox="0 0 24 24" class="size-5 text-sky-300 drop-shadow-[0_0_10px_rgba(56,189,248,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7" />
          </svg>
          选择回复长度
        </button>
        <div v-if="showLength && lengths?.length" class="absolute right-0 mt-2 w-28 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20">
          <button
            v-for="opt in lengths"
            :key="opt.key"
            type="button"
            class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
            @click="onSelectLength?.(opt.key, opt.label)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <button
        type="button"
        @click="onSend"
        :disabled="busy || !value.trim()"
        class="size-11 rounded-2xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] text-white shadow-[var(--glow-blue)] hover:brightness-105 transition-colors inline-flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="发送"
        :title="busy ? '请稍候...' : '发送'"
      >
        <svg viewBox="0 0 24 24" class="size-6 drop-shadow-[0_0_10px_rgba(255,255,255,0.45)]" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

type MenuOption = { key: string; label: string };

const props = defineProps<{
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  busy?: boolean;
  responseLengthText?: string;
  showLength?: boolean;
  lengths?: readonly MenuOption[];
  onToggleLength?: () => void;
  onSelectLength?: (key: string, label: string) => void;
  onSelectInclude?: (include: boolean) => void;
}>();

const includeMaterials = ref(false);
const showInclude = ref(false);

const onInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  props.onChange(target.value);
};

const onToggleLength = () => props.onToggleLength?.();

const toggleInclude = () => {
  showInclude.value = !showInclude.value;
};

const setInclude = (next: boolean) => {
  includeMaterials.value = next;
  showInclude.value = false;
  props.onSelectInclude?.(next);
};
</script>
