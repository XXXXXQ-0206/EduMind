<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-amber-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 5.25h9.75A2.25 2.25 0 0 1 18 7.5v11.25A2.25 2.25 0 0 1 15.75 21H6A2.25 2.25 0 0 1 3.75 18.75V7.5A2.25 2.25 0 0 1 6 5.25Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3.75h9.75A2.25 2.25 0 0 1 20.25 6v11.25" />
          </svg>
        </span>
        历史卡片
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewDeck"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建卡片
      </button>
    </div>
    <div class="grid grid-cols-3 gap-2 mb-3">
      <button
        v-for="item in statusOptions"
        :key="item.key"
        type="button"
        class="rounded-2xl px-2 py-2 text-[11px] font-semibold border transition-colors text-slate-950"
        :class="statusButtonClass(item.key)"
        @click="setStatusFilter(item.key)"
      >
        <div class="flex flex-col items-center gap-0.5">
          <span class="leading-tight">{{ item.label }}</span>
          <span class="text-[10px] font-bold leading-tight">{{ statusCounts[item.key] }}</span>
        </div>
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="decks.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="deck in decks" :key="deck.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
            @click="openDeck(deck.id)"
            @contextmenu.prevent="openContextMenu($event, deck)"
            :title="deck.title || '未命名卡组'"
          >
            <div class="truncate">{{ deck.title || "未命名卡组" }}</div>
            <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">卡片数量：{{ deck.count || 5 }}</div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="toggleDetails(deck.id)"
            aria-label="查看卡片详情"
            :title="'查看卡片详情'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removeDeck(deck.id)"
            aria-label="删除卡片"
            :title="'删除卡片'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
        <div v-if="expandedId === deck.id" class="mt-3 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-3 space-y-3">
          <div v-if="details[deck.id]?.cards?.length" class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <span
                v-for="(card, i) in details[deck.id].cards"
                :key="card.id"
                class="size-8 rounded-full border-2 inline-flex items-center justify-center text-xs font-semibold"
                :class="circleClass(deck.id, card.id)"
              >
                {{ i + 1 }}
              </span>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs text-sky-300 hover:text-sky-200 transition-colors"
              @click.stop="openDeck(deck.id)"
            >
              <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              打开详情
            </button>
          </div>
          <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无卡片详情</div>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史卡片</div>
    <HistoryContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="closeContextMenu"
      @select="addDeckToBag"
    />
  </aside>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deleteKnowledgeDeck, getKnowledgeDeck, listKnowledgeDecks, type KnowledgeDeck } from "../../lib/api";
import { addLearningBagRecord } from "../../lib/learningBag";
import { getUserScopedStorageKey } from "../../lib/userStorage";
import HistoryContextMenu from "../common/HistoryContextMenu.vue";

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const decks = ref<{ id: string; title?: string; count?: number }[]>([]);
const expandedId = ref<string | null>(null);
const details = ref<Record<string, KnowledgeDeck>>({});
const statusMap = ref<Record<string, Record<string, "mastered" | "review" | "pending" | "">>>({});
const statusCounts = ref({ mastered: 0, pending: 0, review: 0 });
const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextTarget = ref<{ id: string; title?: string; count?: number } | null>(null);
const statusOptions = [
  { key: "mastered", label: "标记掌握" },
  { key: "pending", label: "待确认" },
  { key: "review", label: "待复习" },
] as const;

const activeStatus = computed(() => {
  const raw = String(route.query.status || "");
  if (raw === "mastered" || raw === "pending" || raw === "review") return raw;
  return "";
});

const buildQuery = (overrides: Record<string, string | undefined>) => {
  const next: Record<string, string> = {};
  Object.entries(route.query).forEach(([key, value]) => {
    const val = Array.isArray(value) ? value[0] : value;
    if (typeof val === "string" && val) next[key] = val;
  });
  Object.entries(overrides).forEach(([key, value]) => {
    if (value) next[key] = value;
    else delete next[key];
  });
  return next;
};

const loadDecks = async () => {
  loading.value = true;
  try {
    const res = await listKnowledgeDecks();
    decks.value = Array.isArray(res?.decks) ? res.decks : [];
    computeStatusCounts(decks.value);
  } catch {
    decks.value = [];
    statusCounts.value = { mastered: 0, pending: 0, review: 0 };
  } finally {
    loading.value = false;
  }
};

const openDeck = (id: string) => {
  if (!id) return;
  router.push({ path: "/knowledge-cards", query: buildQuery({ deckId: id, t: String(Date.now()) }), state: { deckId: id } });
};

const startNewDeck = () => {
  router.push({ path: "/knowledge-cards", query: buildQuery({ deckId: undefined, t: undefined, status: undefined, new: String(Date.now()) }) });
};

const openContextMenu = (event: MouseEvent, deck: { id: string; title?: string; count?: number }) => {
  contextTarget.value = deck;
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

const addDeckToBag = () => {
  const deck = contextTarget.value;
  if (!deck?.id) return;
  addLearningBagRecord({
    type: "knowledge-card",
    refId: deck.id,
    title: deck.title || "未命名卡组",
    subtitle: `卡片数量：${deck.count || 0}`,
    path: "/knowledge-cards",
    query: { deckId: deck.id },
  });
};

const setStatusFilter = (key: "mastered" | "review" | "pending") => {
  const next = activeStatus.value === key ? undefined : key;
  router.push({
    path: "/knowledge-cards",
    query: buildQuery({ deckId: undefined, t: undefined, new: undefined, status: next }),
  });
};

const statusButtonClass = (key: "mastered" | "review" | "pending") => {
  const isActive = activeStatus.value === key;
  if (key === "mastered") {
    return isActive
      ? "border-emerald-400 bg-emerald-400/25"
      : "border-emerald-300/40 bg-[color:var(--nav-bg)]/40 hover:bg-emerald-400/10";
  }
  if (key === "review") {
    return isActive
      ? "border-amber-400 bg-amber-400/25"
      : "border-amber-300/40 bg-[color:var(--nav-bg)]/40 hover:bg-amber-400/10";
  }
  return isActive
    ? "border-slate-300 bg-white"
    : "border-slate-300/40 bg-[color:var(--nav-bg)]/40 hover:bg-white/10";
};

const toggleDetails = async (id: string) => {
  if (!id) return;
  if (expandedId.value === id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = id;
  if (!details.value[id]) {
    try {
      const res = await getKnowledgeDeck(id);
      if (res?.ok && res.deck) {
        details.value = { ...details.value, [id]: res.deck };
        loadStatus(id);
      }
    } catch {
      return;
    }
  }
};

const loadStatus = (deckId: string) => {
  try {
    const raw = localStorage.getItem(getUserScopedStorageKey(`knowledge-cards:status:${deckId}`));
    const parsed = raw ? JSON.parse(raw) : {};
    statusMap.value = { ...statusMap.value, [deckId]: parsed || {} };
  } catch {
    statusMap.value = { ...statusMap.value, [deckId]: {} };
  }
};

const computeStatusCounts = (items: { id: string; count?: number }[]) => {
  const totals = { mastered: 0, pending: 0, review: 0 };
  items.forEach((deck) => {
    const totalCount = Math.max(0, Number(deck.count || 0));
    let masteredCount = 0;
    let reviewCount = 0;
    try {
      const raw = localStorage.getItem(getUserScopedStorageKey(`knowledge-cards:status:${deck.id}`));
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

const circleClass = (deckId: string, cardId: string) => {
  const status = statusMap.value[deckId]?.[cardId] || "pending";
  if (status === "mastered") return "border-emerald-400 bg-emerald-300/70 text-slate-950";
  if (status === "review") return "border-amber-400 bg-amber-300/70 text-slate-950";
  return "border-slate-400/70 bg-white text-slate-950";
};

const removeDeck = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该卡组吗？");
  if (!ok) return;
  const prev = decks.value;
  decks.value = prev.filter((item) => item.id !== id);
  try {
    await deleteKnowledgeDeck(id);
    if ((route.query.deckId as string) === id) {
      router.push({ path: "/knowledge-cards" });
    }
    await loadDecks();
  } catch {
    decks.value = prev;
  }
};

onMounted(() => {
  loadDecks();
  window.addEventListener("knowledge-cards:updated", loadDecks as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("knowledge-cards:updated", loadDecks as EventListener);
});
</script>
