<template>
  <div class="min-h-screen w-full px-4 lg:pl-28 lg:pr-4">
    <div class="max-w-6xl mx-auto pt-6 pb-14 px-2">
      <div class="glass-card rounded-3xl border border-[color:var(--glass-border)] p-4 md:p-5 mb-6 shadow-[0_14px_32px_rgba(0,0,0,0.25)] bg-gradient-to-br from-sky-500/10 via-transparent to-violet-500/10">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">我的学习袋</h1>
            <div class="text-xs text-[color:var(--nav-text-muted)] mt-1">
              收藏 {{ historyItems.length }} 条<span v-if="items.length"> · 学习卡片 {{ items.length }} 张</span>
            </div>
            <p class="text-xs text-[color:var(--nav-text-muted)]/90 mt-2 leading-relaxed max-w-2xl">
              汇总你收藏的学习成果与重点卡片，支持快速回看、分类对比和后续复习安排。
            </p>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-300/70 border border-rose-200 text-slate-950 font-semibold shadow-[0_8px_20px_rgba(190,24,93,0.25)] hover:bg-rose-300/80 hover:border-rose-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="busy || (!items.length && !historyItems.length)"
            @click="clearAll"
          >
            <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
            清空全部
          </button>
        </div>
      </div>

      <div v-if="historyItems.length" class="glass-card rounded-3xl border border-[color:var(--glass-border)] p-4 md:p-4 mb-6 shadow-[0_14px_32px_rgba(0,0,0,0.22)]">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="text-sm text-[color:var(--app-text)] font-black">收藏统计</div>
            <div class="text-xs text-[color:var(--nav-text-muted)] mt-1">按五类收藏进行数量分布</div>
          </div>
          <div class="text-xs text-[color:var(--nav-text-muted)] font-black">总计 {{ favoriteTotal }} 条</div>
        </div>

        <div class="grid lg:grid-cols-[220px_1fr] gap-4 mt-3">
          <div class="flex items-center justify-center">
            <div class="relative size-36">
              <svg viewBox="0 0 120 120" class="size-36 -rotate-90">
                <circle cx="60" cy="60" r="42" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="16" />
                <circle
                  v-for="seg in pieSegments"
                  :key="seg.type"
                  cx="60"
                  cy="60"
                  r="42"
                  fill="none"
                  :stroke="seg.color"
                  stroke-width="16"
                  stroke-linecap="butt"
                  :stroke-dasharray="seg.dasharray"
                  :stroke-dashoffset="seg.dashoffset"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center flex-col">
                <div class="text-lg font-black text-[color:var(--app-text)]">{{ favoriteTotal }}</div>
                <div class="text-[10px] text-[color:var(--nav-text-muted)] font-black">收藏总数</div>
              </div>
            </div>
          </div>

          <div class="space-y-2.5">
            <div
              v-for="row in statsRows"
              :key="row.type"
              class="rounded-xl border bg-[color:var(--glass-bg)]/70 px-3 py-2"
              :style="{ borderColor: row.chartBorderColor, backgroundImage: row.rowBackground }"
            >
              <div class="flex items-center justify-between gap-2 mb-1.5">
                <div class="inline-flex items-center gap-2 text-sm text-[color:var(--app-text)] font-black">
                  <span class="size-2.5 rounded-full" :style="{ backgroundColor: row.chartColor }"></span>
                  {{ row.label }}
                </div>
                <div class="text-xs text-[color:var(--nav-text)] font-black">{{ row.count }}</div>
              </div>
              <div class="h-1.5 rounded-full bg-white/10 border overflow-hidden" :style="{ borderColor: row.trackBorderColor }">
                <div
                  class="h-full rounded-full transition-all duration-300 shadow-[0_0_12px_rgba(255,255,255,0.2)]"
                  :style="{ width: `${row.percent}%`, backgroundColor: row.chartColor }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="historyItems.length" class="mb-8">
        <div class="text-sm text-[color:var(--nav-text)] mb-3 font-semibold">收藏记录</div>
        <div class="grid md:grid-cols-2 gap-4">
          <div
            v-for="it in historyItems"
            :key="it.id"
            class="rounded-2xl glass-card border border-[color:var(--glass-border)] p-4 cursor-pointer hover:bg-white/10 transition-colors"
            @click="openHistory(it)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] mb-2 font-black" :class="typeBadgeClass(it.type)">
                  <span class="inline-flex items-center" v-html="typeIcon(it.type)"></span>
                  {{ typeLabel(it.type) }}
                </div>
                <div class="text-[color:var(--app-text)] font-medium">{{ it.title }}</div>
                <div v-if="it.subtitle" class="text-[color:var(--nav-text-muted)] text-xs mt-1">{{ it.subtitle }}</div>
              </div>
              <button
                type="button"
                class="p-2 rounded-lg border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 hover:bg-white/10 disabled:opacity-50"
                aria-label="Delete"
                :disabled="busy"
                @click.stop="removeHistory(it.id)"
              >
                <svg class="size-4 text-[color:var(--nav-text)]" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9.75 9.75a.75.75 0 0 1 .75.75v6a.75.75 0 1 1-1.5 0v-6a.75.75 0 0 1 .75-.75Zm3.75.75a.75.75 0 0 0-1.5 0v6a.75.75 0 1 0 1.5 0v-6Z" />
                  <path fill-rule="evenodd" d="M3 6.75A.75.75 0 0 1 3.75 6h4.443A2.25 2.25 0 0 1 10.315 4.5h2.37A2.25 2.25 0 0 1 14.807 6H19.5a.75.75 0 0 1 0 1.5h-.708l-1.03 12.06A2.25 2.25 0 0 1 15.52 21H8.48a2.25 2.25 0 0 1-2.242-2.44L5.208 7.5H4.5A.75.75 0 0 1 3.75 6.75ZM9.75 6a.75.75 0 0 1 .671-.75h2.37a.75.75 0 0 1 .671.75H9.75Z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="items.length" class="text-sm text-[color:var(--nav-text)] mb-3 font-semibold">学习卡片</div>
      <div class="grid md:grid-cols-2 gap-4">
        <div v-for="it in items" :key="it.id" class="rounded-2xl glass-card border border-[color:var(--glass-border)] p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)] mb-1">
                {{ it.tag === 'note' ? 'note' : 'flashcard' }}
              </div>
              <div class="text-[color:var(--app-text)] font-medium">{{ it.question }}</div>
            </div>
            <button
              type="button"
              class="p-2 rounded-lg border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 hover:bg-white/10 disabled:opacity-50"
              aria-label="Delete"
              :disabled="busy"
              @click="remove(it.id)"
            >
              <svg class="size-4 text-[color:var(--nav-text)]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9.75 9.75a.75.75 0 0 1 .75.75v6a.75.75 0 1 1-1.5 0v-6a.75.75 0 0 1 .75-.75Zm3.75.75a.75.75 0 0 0-1.5 0v6a.75.75 0 1 0 1.5 0v-6Z" />
                <path fill-rule="evenodd" d="M3 6.75A.75.75 0 0 1 3.75 6h4.443A2.25 2.25 0 0 1 10.315 4.5h2.37A2.25 2.25 0 0 1 14.807 6H19.5a.75.75 0 0 1 0 1.5h-.708l-1.03 12.06A2.25 2.25 0 0 1 15.52 21H8.48a2.25 2.25 0 0 1-2.242-2.44L5.208 7.5H4.5A.75.75 0 0 1 3.75 6.75ZM9.75 6a.75.75 0 0 1 .671-.75h2.37a.75.75 0 0 1 .671.75H9.75Z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
          <div class="text-[color:var(--nav-text)] text-sm mt-2 whitespace-pre-wrap">{{ it.answer }}</div>
        </div>
      </div>

      <div v-if="!items.length && !historyItems.length" class="mt-16 text-center text-[color:var(--nav-text-muted)]">
        您的学习袋是空的。请在历史记录中右键添加收藏。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { deleteFlashcard, listFlashcards, type SavedFlashcard } from "../lib/api";
import {
  clearLearningBagRecords,
  learningBagTypeLabel,
  listLearningBagRecords,
  removeLearningBagRecord,
  type LearningBagRecord,
} from "../lib/learningBag";

const router = useRouter();
const items = ref<SavedFlashcard[]>([]);
const historyItems = ref<LearningBagRecord[]>([]);
const busy = ref(false);

const typeStyles: Record<
  LearningBagRecord["type"],
  { label: string; badgeClass: string; chartColor: string; icon: string }
> = {
  chat: {
    label: "对话",
    badgeClass: "border-sky-300/60 bg-sky-300/70 text-slate-950",
    chartColor: "#38bdf8",
    icon: '<svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z"/></svg>',
  },
  note: {
    label: "智能笔记",
    badgeClass: "border-emerald-300/60 bg-emerald-300/70 text-slate-950",
    chartColor: "#34d399",
    icon: '<svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v10.5H5.25z"/><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75v-1.5h7.5v1.5"/></svg>',
  },
  podcast: {
    label: "AI播客",
    badgeClass: "border-violet-300/60 bg-violet-300/70 text-slate-950",
    chartColor: "#a78bfa",
    icon: '<svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4a6 6 0 0 0-6 6v2a6 6 0 0 0 12 0v-2a6 6 0 0 0-6-6Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M9.5 19.5h5"/></svg>',
  },
  quiz: {
    label: "测验",
    badgeClass: "border-amber-300/70 bg-amber-300/80 text-slate-950",
    chartColor: "#f59e0b",
    icon: '<svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3.5a6.5 6.5 0 0 0-3.5 11.98V17.5h7v-2.02A6.5 6.5 0 0 0 12 3.5Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M9.5 20.5h5"/></svg>',
  },
  "knowledge-card": {
    label: "知识卡片",
    badgeClass: "border-rose-300/70 bg-rose-300/80 text-slate-950",
    chartColor: "#fb7185",
    icon: '<svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10A2.5 2.5 0 0 1 19.5 7v10A2.5 2.5 0 0 1 17 19.5H7A2.5 2.5 0 0 1 4.5 17V7A2.5 2.5 0 0 1 7 4.5Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M8.5 8.5h7"/></svg>',
  },
};

const typeOrder: LearningBagRecord["type"][] = ["chat", "note", "podcast", "quiz", "knowledge-card"];

const favoriteTotal = computed(() => historyItems.value.length);

const typeCounts = computed(() => {
  const map: Record<LearningBagRecord["type"], number> = {
    chat: 0,
    note: 0,
    podcast: 0,
    quiz: 0,
    "knowledge-card": 0,
  };
  historyItems.value.forEach((item) => {
    map[item.type] += 1;
  });
  return map;
});

const hexToRgba = (hex: string, alpha: number) => {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3 ? normalized.split("").map((char) => char + char).join("") : normalized;
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const statsRows = computed(() => {
  const max = Math.max(1, ...typeOrder.map((type) => typeCounts.value[type]));
  return typeOrder.map((type) => ({
    type,
    label: typeStyles[type].label,
    count: typeCounts.value[type],
    chartColor: typeStyles[type].chartColor,
    chartBorderColor: hexToRgba(typeStyles[type].chartColor, 0.45),
    trackBorderColor: hexToRgba(typeStyles[type].chartColor, 0.35),
    rowBackground: `linear-gradient(120deg, ${hexToRgba(typeStyles[type].chartColor, 0.16)} 0%, rgba(255,255,255,0.02) 55%, transparent 100%)`,
    percent: Math.round((typeCounts.value[type] / max) * 100),
  }));
});

const pieSegments = computed(() => {
  const total = favoriteTotal.value || 1;
  const radius = 42;
  const c = 2 * Math.PI * radius;
  let acc = 0;
  return typeOrder
    .filter((type) => typeCounts.value[type] > 0)
    .map((type) => {
      const value = typeCounts.value[type];
      const length = (value / total) * c;
      const segment = {
        type,
        color: typeStyles[type].chartColor,
        dasharray: `${length} ${Math.max(c - length, 0)}`,
        dashoffset: -acc,
      };
      acc += length;
      return segment;
    });
});

const load = async () => {
  try {
    const { flashcards } = await listFlashcards();
    items.value = (flashcards || []).sort((a, b) => b.created - a.created);
  } catch {
    items.value = [];
  }
  historyItems.value = listLearningBagRecords();
};

const remove = async (id: string) => {
  busy.value = true;
  try {
    await deleteFlashcard(id);
  } catch {
    return;
  } finally {
    await load();
    busy.value = false;
  }
};

const removeHistory = async (id: string) => {
  busy.value = true;
  try {
    removeLearningBagRecord(id);
  } finally {
    await load();
    busy.value = false;
  }
};

const openHistory = (item: LearningBagRecord) => {
  router.push({ path: item.path, query: item.query || {} });
};

const typeLabel = (type: LearningBagRecord["type"]) => learningBagTypeLabel(type);
const typeBadgeClass = (type: LearningBagRecord["type"]) => typeStyles[type].badgeClass;
const typeIcon = (type: LearningBagRecord["type"]) => typeStyles[type].icon;

const clearAll = async () => {
  if (!items.value.length && !historyItems.value.length) return;
  busy.value = true;
  try {
    await Promise.all(items.value.map((i) => deleteFlashcard(i.id).catch(() => undefined)));
    clearLearningBagRecords();
  } catch {
    return;
  } finally {
    await load();
    busy.value = false;
  }
};

const onLearningBagUpdated = () => {
  historyItems.value = listLearningBagRecords();
};

onMounted(() => {
  load();
  window.addEventListener("learning-bag:updated", onLearningBagUpdated as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("learning-bag:updated", onLearningBagUpdated as EventListener);
});
</script>
