<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" />
          </svg>
        </span>
        历史试卷
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewPaper"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建试卷
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="papers.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="p in papers" :key="p.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
            @click="openPaper(p.id)"
            :title="p.title || '未命名试卷'"
          >
            <div class="truncate">{{ p.title || "未命名试卷" }}</div>
            <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">
              选择{{ p.count_choice ?? 0 }}·填空{{ p.count_fill ?? 0 }}·应用{{ p.count_application ?? 0 }}
            </div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="openPreview(p.id)"
            aria-label="预览试卷"
            title="预览试卷"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removePaper(p.id)"
            aria-label="删除试卷"
            title="删除试卷"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
            </svg>
          </button>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史试卷</div>
    <PaperPreviewModal :visible="previewVisible" :paper-id="previewPaperId" @close="closePreview" />
  </aside>
</template>

<script setup lang="ts">
import { inject, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deletePaper, listPapers } from "../../lib/api";
import PaperPreviewModal from "./PaperPreviewModal.vue";

const router = useRouter();
const route = useRoute();
const paperListVersion = inject<{ value: number } | undefined>("paperListVersion");
const loading = ref(false);
const papers = ref<{ id: string; title?: string; count_choice?: number; count_fill?: number; count_application?: number; at?: number }[]>([]);
const previewVisible = ref(false);
const previewPaperId = ref<string | null>(null);

function openPreview(id: string) {
  if (!id) return;
  previewPaperId.value = id;
  previewVisible.value = true;
}

function closePreview() {
  previewVisible.value = false;
  previewPaperId.value = null;
}

const loadPapers = async () => {
  loading.value = true;
  try {
    const res = await listPapers();
    papers.value = Array.isArray(res?.papers) ? res.papers : [];
  } catch {
    papers.value = [];
  } finally {
    loading.value = false;
  }
};

const openPaper = (id: string) => {
  if (!id) return;
  router.push({ path: "/teacher/paper", query: { paperId: id }, state: { paperId: id } });
};

const startNewPaper = () => {
  router.push({ path: "/teacher/paper", query: { new: String(Date.now()) } });
};

const removePaper = async (id: string) => {
  if (!id) return;
  if (!window.confirm("确定删除该试卷吗？")) return;
  const prev = papers.value;
  papers.value = prev.filter((item) => item.id !== id);
  try {
    await deletePaper(id);
    if ((route.query.paperId as string) === id) {
      router.push({ path: "/teacher/paper" });
    }
    await loadPapers();
  } catch {
    papers.value = prev;
  }
};

onMounted(loadPapers);
watch(() => paperListVersion?.value ?? 0, () => loadPapers());
</script>
