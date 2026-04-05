<template>
  <div :class="containerClass">
    <div class="max-w-4xl mx-auto">
      <div class="relative rounded-3xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-[0_14px_30px_rgba(15,23,42,0.12),0_1px_0_rgba(255,255,255,0.5)] backdrop-blur-lg p-3 focus-within:shadow-[0_0_0_2px_rgba(251,191,36,0.45),0_18px_40px_rgba(251,191,36,0.22)]">
        <span class="ai-spark ai-spark--right" aria-hidden="true"></span>
        <div class="flex flex-wrap items-center justify-end gap-2 pb-3">
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
            aria-label="回复长度"
            :title="responseLengthText ? `选择回复长度：${responseLengthText}` : '选择回复长度'"
            @click="onToggleLength"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-sky-300 drop-shadow-[0_0_10px_rgba(56,189,248,0.6)]" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7" />
            </svg>
            {{ responseLengthText ? `选择回复长度：${responseLengthText}` : "选择回复长度" }}
          </button>
          <div
            v-if="showLength && lengths?.length"
            class="absolute right-0 mt-2 w-28 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20"
          >
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
          class="h-10 px-4 rounded-2xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] text-white shadow-[var(--glow-blue)] hover:brightness-105 transition-colors inline-flex items-center justify-center"
          aria-label="发送"
          :title="props.disabled ? '请稍候...' : '发送'"
          @click="onSubmit"
        >
          <svg viewBox="0 0 24 24" class="size-6 drop-shadow-[0_0_10px_rgba(255,255,255,0.45)]" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
          </svg>
        </button>
      </div>
        <textarea
          ref="inputRef"
          placeholder="提出后续问题或请求更多示例..."
          rows="1"
          class="w-full text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/75 placeholder:text-[color:var(--nav-text-muted)] rounded-2xl p-4 outline-none resize-none overflow-y-auto max-h-64 min-h-[2.75rem] transition-colors focus:bg-[color:var(--nav-bg)]/90"
          @keydown.enter.exact.prevent="onSubmit"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

type MenuOption = { key: string; label: string };

const props = defineProps<{
  disabled?: boolean;
  onSend: (text: string) => void;
  responseLengthText?: string;
  showLength?: boolean;
  lengths?: readonly MenuOption[];
  onToggleLength?: () => void;
  onSelectLength?: (key: string, label: string) => void;
  onSelectInclude?: (include: boolean) => void;
  inline?: boolean;
}>();

const inputRef = ref<HTMLTextAreaElement | null>(null);
const includeMaterials = ref(false);
const showInclude = ref(false);

const containerClass = computed(() =>
  props.inline
    ? "relative w-full mt-8"
    : "fixed bottom-0 pt-6 pb-4 border-t border-[color:var(--glass-border)] left-4 right-4 lg:left-32 lg:right-4 z-40 bg-[color:var(--app-bg-1)]/80 backdrop-blur-xl"
);

const onResize = () => {
  const el = inputRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 256) + "px";
};

const onSubmit = () => {
  if (props.disabled) return;
  const el = inputRef.value;
  if (!el) return;
  const value = el.value.trim();
  if (!value) return;
  props.onSend(value);
  el.value = "";
  onResize();
};

const toggleInclude = () => {
  showInclude.value = !showInclude.value;
};

const setInclude = (next: boolean) => {
  includeMaterials.value = next;
  showInclude.value = false;
  props.onSelectInclude?.(next);
};

onMounted(() => {
  const el = inputRef.value;
  if (!el) return;
  el.addEventListener("input", onResize);
  onResize();
});

onBeforeUnmount(() => {
  const el = inputRef.value;
  if (!el) return;
  el.removeEventListener("input", onResize);
});
</script>
