<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      @click.self="onClose"
    >
      <div class="bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh] w-full" style="max-width: 210mm;">
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 shrink-0">
          <span class="font-bold text-slate-800" style="font-family: 黑体, SimHei, sans-serif;">试卷预览</span>
          <button
            type="button"
            class="p-2 rounded-xl hover:bg-slate-100 text-slate-600"
            aria-label="关闭"
            @click="onClose"
          >
            <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div class="overflow-y-auto flex-1 p-6">
          <div v-if="loading" class="text-slate-500 py-8 text-center">加载中…</div>
          <div
            v-else-if="questions.length"
            class="paper-a4 bg-white text-black rounded-lg p-6 shadow-inner"
            style="width: 210mm; min-height: 297mm; box-sizing: border-box; font-family: 宋体, SimSun, serif;"
          >
            <h1 class="text-xl font-bold text-center mb-6 pb-2 border-b-2 border-slate-300" style="font-family: 黑体, SimHei, sans-serif;">{{ title || '试卷' }}</h1>
            <template v-for="group in questionsByType" :key="group.type">
              <div class="mb-6">
                <div class="text-base font-bold border-2 border-slate-400 rounded-lg px-4 py-2 mb-4 bg-slate-100 text-slate-800" style="font-family: 黑体, SimHei, sans-serif;">
                  {{ group.label }}
                </div>
                <div class="space-y-4">
                  <div
                    v-for="(item, i) in group.items"
                    :key="item.id"
                    class="text-sm"
                  >
                    <div class="flex gap-2 mb-1">
                      <span class="font-bold shrink-0" style="font-family: 黑体, SimHei, sans-serif;">{{ item.id }}.</span>
                      <span class="font-bold text-slate-700" style="font-family: 黑体, SimHei, sans-serif;">{{ typeLabel(item.type) }}</span>
                    </div>
                    <p class="mb-2 pl-5">{{ item.question }}</p>
                    <div v-if="item.type === 'choice' && item.options?.length" class="pl-5 space-y-1">
                      <p v-for="(opt, j) in item.options" :key="j" class="pl-4">{{ String.fromCharCode(65 + j) }}. {{ opt }}</p>
                    </div>
                    <div v-if="item.type !== 'choice' && item.answer" class="pl-5 mt-2 p-2 bg-slate-50 rounded text-slate-700">
                      <span class="font-bold" style="font-family: 黑体, SimHei, sans-serif;">参考答案：</span>{{ item.answer }}
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
          <div v-else-if="!loading" class="text-slate-500 py-8 text-center">暂无题目</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { getPaperDetail } from "../../lib/api";
import type { PaperItem } from "../../lib/api";

const props = defineProps<{
  visible: boolean;
  paperId: string | null;
}>();

const emit = defineEmits<{ (e: "close"): void }>();

const title = ref("");
const questions = ref<PaperItem[]>([]);
const loading = ref(false);

function typeLabel(t: string) {
  if (t === "choice") return "选择题";
  if (t === "fill") return "填空题";
  if (t === "application") return "应用题";
  return t;
}

const questionsByType = computed(() => {
  const order: ("choice" | "fill" | "application")[] = ["choice", "fill", "application"];
  const labels: Record<string, string> = { choice: "选择题", fill: "填空题", application: "应用题" };
  const groups: { type: string; label: string; items: PaperItem[] }[] = [];
  for (const t of order) {
    const items = questions.value.filter((q) => q.type === t);
    if (items.length) groups.push({ type: t, label: labels[t], items });
  }
  return groups;
});

async function load() {
  if (!props.paperId) {
    questions.value = [];
    title.value = "";
    return;
  }
  loading.value = true;
  try {
    const res = await getPaperDetail(props.paperId);
    if (res?.ok) {
      title.value = res.paper?.title ?? "";
      questions.value = Array.isArray(res.questions) ? res.questions : [];
    } else {
      questions.value = [];
      title.value = "";
    }
  } catch {
    questions.value = [];
    title.value = "";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.visible, props.paperId] as const,
  ([v, id]) => {
    if (v && id) load();
  },
  { immediate: true }
);

function onClose() {
  emit("close");
}
</script>
