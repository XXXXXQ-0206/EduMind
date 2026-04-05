<template>
  <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 mb-8 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2"
            :title="includeMaterialsValue ? '备课资料：是' : '备课资料：否'"
            @click="toggleInclude"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-amber-300" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
            </svg>
            备课资料：{{ includeMaterialsValue ? "是" : "否" }}
          </button>
          <div v-if="showInclude" class="absolute right-0 mt-2 w-24 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20">
            <button type="button" class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]" @click="setInclude(true)">是</button>
            <button type="button" class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]" @click="setInclude(false)">否</button>
          </div>
        </div>
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2"
            :title="'难度：' + difficultyLabel"
            @click="toggleDifficulty"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75v16.5m7.5-7.5h-15" />
            </svg>
            难度：{{ difficultyLabel }}
          </button>
          <div v-if="showDifficulty" class="absolute right-0 mt-2 w-28 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20">
            <button v-for="opt in difficultyOpts" :key="opt.value" type="button" class="w-full text-left px-3 py-2 text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]" @click="setDifficulty(opt.value)">{{ opt.label }}</button>
          </div>
        </div>
        <div class="relative">
          <button
            type="button"
            class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2"
            title="题型与数量"
            @click="toggleCounts"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7" />
            </svg>
            选择{{ countChoice }}·填空{{ countFill }}·应用{{ countApplication }}
          </button>
          <div v-if="showCounts" class="absolute right-0 mt-2 w-56 bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] rounded-2xl shadow-lg overflow-hidden z-20 p-3 space-y-2">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs text-[color:var(--nav-text-muted)]">选择题</span>
              <input v-model.number="localChoice" type="number" min="0" max="30" class="w-16 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] px-2 py-1 text-xs text-[color:var(--app-text)]" />
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs text-[color:var(--nav-text-muted)]">填空题</span>
              <input v-model.number="localFill" type="number" min="0" max="20" class="w-16 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] px-2 py-1 text-xs text-[color:var(--app-text)]" />
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs text-[color:var(--nav-text-muted)]">应用题</span>
              <input v-model.number="localApplication" type="number" min="0" max="20" class="w-16 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] px-2 py-1 text-xs text-[color:var(--app-text)]" />
            </div>
            <button type="button" class="w-full rounded-xl bg-[color:var(--nav-hover-bg)] py-1.5 text-xs text-[color:var(--app-text)]" @click="applyCounts">确定</button>
          </div>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 items-stretch">
        <input
          :value="value"
          @input="onInput"
          placeholder="输入主题生成试卷（例如：一元二次方程）"
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
            生成试卷
            <svg viewBox="0 0 24 24" class="size-4" fill="none">
              <path d="M3 12l18-9-6.75 9L21 21 3 12z" fill="currentColor" />
            </svg>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

type Difficulty = "easy" | "medium" | "hard";

const props = withDefaults(
  defineProps<{
    value: string;
    onChange: (v: string) => void;
    onStart: () => void;
    isLoading?: boolean;
    onSelectInclude?: (include: boolean) => void;
    onSelectDifficulty?: (d: Difficulty) => void;
    onSelectCounts?: (c: { choice: number; fill: number; application: number }) => void;
    includeMaterials?: boolean;
    difficulty?: Difficulty;
    countChoice?: number;
    countFill?: number;
    countApplication?: number;
  }>(),
  { isLoading: false, includeMaterials: false, difficulty: "medium", countChoice: 10, countFill: 5, countApplication: 2 }
);

const emit = defineEmits<{ (e: "update:includeMaterials", v: boolean): void; (e: "update:difficulty", v: Difficulty): void }>();

const difficultyOpts: { value: Difficulty; label: string }[] = [
  { value: "easy", label: "简单" },
  { value: "medium", label: "中等" },
  { value: "hard", label: "困难" },
];

const disabled = computed(() => !props.value.trim() || props.isLoading);
const includeMaterialsValue = computed(() => props.includeMaterials);
const showInclude = ref(false);
const showDifficulty = ref(false);
const showCounts = ref(false);
const difficultyLabel = computed(() => difficultyOpts.find((o) => o.value === props.difficulty)?.label ?? "中等");

const localChoice = ref(props.countChoice);
const localFill = ref(props.countFill);
const localApplication = ref(props.countApplication);
watch([() => props.countChoice, () => props.countFill, () => props.countApplication], ([c, f, a]) => {
  localChoice.value = Number(c) || 10;
  localFill.value = Number(f) || 5;
  localApplication.value = Number(a) || 2;
});

function toggleInclude() {
  showInclude.value = !showInclude.value;
}
function setInclude(v: boolean) {
  showInclude.value = false;
  props.onSelectInclude?.(v);
  emit("update:includeMaterials", v);
}
function toggleDifficulty() {
  showDifficulty.value = !showDifficulty.value;
}
function setDifficulty(v: Difficulty) {
  showDifficulty.value = false;
  props.onSelectDifficulty?.(v);
  emit("update:difficulty", v);
}
function toggleCounts() {
  localChoice.value = props.countChoice;
  localFill.value = props.countFill;
  localApplication.value = props.countApplication;
  showCounts.value = !showCounts.value;
}
function applyCounts() {
  const c = Math.max(0, Math.min(30, Number(localChoice.value) || 0));
  const f = Math.max(0, Math.min(20, Number(localFill.value) || 0));
  const a = Math.max(0, Math.min(20, Number(localApplication.value) || 0));
  showCounts.value = false;
  props.onSelectCounts?.({ choice: c, fill: f, application: a });
}

const onInput = (e: Event) => {
  props.onChange((e.target as HTMLInputElement).value);
};
</script>
