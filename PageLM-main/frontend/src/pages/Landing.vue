<template>
  <div class="flex flex-col min-h-screen w-full px-4 lg:pl-28 lg:pr-4 relative overflow-hidden">
    <div class="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none"></div>
    <div class="absolute inset-0 bg-circuit-pattern opacity-15 pointer-events-none"></div>

    <div class="absolute top-0 left-1/4 w-96 h-96 bg-[#00f5ff]/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow"></div>
    <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-[#ff6b35]/15 rounded-full blur-3xl pointer-events-none animate-pulse-glow-orange"></div>

    <div class="absolute top-1/2 left-1/3 w-64 h-64 bg-[#00f5ff]/8 rounded-full blur-3xl pointer-events-none" :style="{ animation: 'float 10s ease-in-out infinite' }"></div>
    <div class="absolute bottom-1/3 right-1/3 w-72 h-72 bg-[#ff6b35]/8 rounded-full blur-3xl pointer-events-none" :style="{ animation: 'float 12s ease-in-out infinite reverse' }"></div>

    <div class="flex-1 flex flex-col justify-center max-w-6xl mx-auto my-20 md:my-4 w-full px-2 relative z-10">
      <div class="flex flex-col lg:flex-row gap-6">
        <LearningFolderPanel class="lg:sticky lg:top-24 lg:self-start" />
        <div class="flex-1">
          <PromptBox
            :value="prompt"
            :onChange="setPrompt"
            :onSend="send"
            :busy="busy"
            :responseLengthText="responseLengthText"
            :showLength="showLength"
            :lengths="lengths"
            :onToggleLength="toggleLength"
            :onSelectLength="selectLength"
          />
          <div class="mt-6 rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-5 shadow-[0_16px_36px_rgba(15,23,42,0.18)]">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">知识卡片</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">掌握度快捷复习</div>
              </div>
              <button
                type="button"
                class="text-xs font-semibold text-slate-950 border border-[color:var(--nav-border)] rounded-full px-3 py-1.5 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors"
                @click="refreshStatusCounts"
              >
                刷新统计
              </button>
            </div>
            <div class="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                class="rounded-2xl border border-emerald-300/50 bg-emerald-400/20 px-4 py-3 text-slate-950 font-semibold transition-colors hover:bg-emerald-400/30"
                @click="goToStatus('mastered')"
              >
                <div class="flex items-center justify-between">
                  <span class="inline-flex items-center gap-2">
                    <svg viewBox="0 0 24 24" class="size-5 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75l2.25 2.25L15 9.75" />
                      <circle cx="12" cy="12" r="9" />
                    </svg>
                    标记掌握
                  </span>
                  <span class="text-sm font-bold">{{ statusCounts.mastered }}</span>
                </div>
              </button>
              <button
                type="button"
                class="rounded-2xl border border-slate-300/60 bg-white/70 px-4 py-3 text-slate-950 font-semibold transition-colors hover:bg-white"
                @click="goToStatus('pending')"
              >
                <div class="flex items-center justify-between">
                  <span class="inline-flex items-center gap-2">
                    <svg viewBox="0 0 24 24" class="size-5 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 8.25a3 3 0 0 1 3 3c0 1.5-.75 2.25-1.5 2.75-.75.5-1.5 1-1.5 2v.75" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5h.008" />
                      <circle cx="12" cy="12" r="9" />
                    </svg>
                    待确认
                  </span>
                  <span class="text-sm font-bold">{{ statusCounts.pending }}</span>
                </div>
              </button>
              <button
                type="button"
                class="rounded-2xl border border-amber-300/60 bg-amber-400/20 px-4 py-3 text-slate-950 font-semibold transition-colors hover:bg-amber-400/30"
                @click="goToStatus('review')"
              >
                <div class="flex items-center justify-between">
                  <span class="inline-flex items-center gap-2">
                    <svg viewBox="0 0 24 24" class="size-5 text-amber-600" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                      <circle cx="12" cy="12" r="9" />
                    </svg>
                    待复习
                  </span>
                  <span class="text-sm font-bold">{{ statusCounts.review }}</span>
                </div>
              </button>
            </div>
            <div v-if="loadingCounts" class="mt-2 text-xs text-[color:var(--nav-text-muted)]">统计更新中...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import PromptBox from "../components/Landing/PromptBox.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import { chatJSON, listKnowledgeDecks } from "../lib/api";

const prompt = ref("");
const responseLength = ref<"Short" | "Medium" | "Long">("Short");
const responseLengthText = ref<"简短" | "中等" | "详细">("简短");
const showLength = ref(false);
const busy = ref(false);
const router = useRouter();
const loadingCounts = ref(false);
const statusCounts = ref({ mastered: 0, pending: 0, review: 0 });

const lengths = [
  { key: "Short", label: "简短" },
  { key: "Medium", label: "中等" },
  { key: "Long", label: "详细" },
] as const;

const normalizeLength = (value: string) => {
  if (value === "Long" || value === "Medium" || value === "Short") return value;
  return "Short";
};

const labelForLength = (key: "Short" | "Medium" | "Long"): "简短" | "中等" | "详细" => {
  if (key === "Long") return "详细";
  if (key === "Medium") return "中等";
  return "简短";
};

const setPrompt = (v: string) => {
  prompt.value = v;
};

const selectLength = (next: string, label: string) => {
  const normalized = normalizeLength(String(next));
  responseLength.value = normalized;
  responseLengthText.value = (label === "简短" || label === "中等" || label === "详细") ? label : labelForLength(normalized);
  showLength.value = false;
};

const toggleLength = () => {
  showLength.value = !showLength.value;
};

const send = async (override?: string) => {
  if (busy.value) return;
  const q = (override ?? prompt.value).trim();
  if (!q) return;

  busy.value = true;
  try {
    const r = await chatJSON({ q, length: responseLength.value });
    router.push({
      path: "/chat",
      query: { chatId: r.chatId, q, length: responseLength.value },
    });
  } finally {
    busy.value = false;
  }
};

const computeStatusCounts = (items: { id: string; count?: number }[]) => {
  const totals = { mastered: 0, pending: 0, review: 0 };
  items.forEach((deck) => {
    const totalCount = Math.max(0, Number(deck.count || 0));
    let masteredCount = 0;
    let reviewCount = 0;
    try {
      const raw = localStorage.getItem(`knowledge-cards:status:${deck.id}`);
      const parsed = raw ? JSON.parse(raw) : {};
      Object.values(parsed || {}).forEach((status) => {
        if (status === "mastered") masteredCount += 1;
        else if (status === "review") reviewCount += 1;
      });
    } catch {
      masteredCount = 0;
      reviewCount = 0;
    }
    totals.mastered += masteredCount;
    totals.review += reviewCount;
    totals.pending += Math.max(0, totalCount - masteredCount - reviewCount);
  });
  statusCounts.value = totals;
};

const refreshStatusCounts = async () => {
  loadingCounts.value = true;
  try {
    const res = await listKnowledgeDecks();
    const metas = Array.isArray(res?.decks) ? res.decks : [];
    computeStatusCounts(metas);
  } catch {
    statusCounts.value = { mastered: 0, pending: 0, review: 0 };
  } finally {
    loadingCounts.value = false;
  }
};

const goToStatus = (status: "mastered" | "pending" | "review") => {
  router.push({ path: "/knowledge-cards", query: { status, t: String(Date.now()) } });
};

onMounted(() => {
  refreshStatusCounts();
  window.addEventListener("knowledge-cards:updated", refreshStatusCounts as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("knowledge-cards:updated", refreshStatusCounts as EventListener);
});
</script>
