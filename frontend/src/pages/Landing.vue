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
          <!-- 替换：原自定义知识卡片快捷区 → MUI Paper/Button/LinearProgress，功能已保留 -->
          <MuiKnowledgeStatusAdapter
            :counts="statusCounts"
            :loading="loadingCounts"
            :mode="themeStore.mode"
            @refresh="refreshStatusCounts"
            @status-click="goToStatus"
          />
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
import MuiKnowledgeStatusAdapter from "../components/mui/MuiKnowledgeStatusAdapter.vue";
import { chatJSON, listKnowledgeDecks } from "../lib/api";
import { useThemeStore } from "../stores/theme";

const prompt = ref("");
const responseLength = ref<"Short" | "Medium" | "Long">("Short");
const responseLengthText = ref<"简短" | "中等" | "详细">("简短");
const showLength = ref(false);
const busy = ref(false);
const router = useRouter();
const themeStore = useThemeStore();
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
