<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <PaperHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)] flex items-center gap-3">试卷</h1>
          </div>

          <!-- 空状态：快捷主题 + 功能介绍 + PaperTopicBar -->
          <div
            v-if="questions.length === 0 && !connecting && !done"
            class="min-h-[62vh] flex flex-col items-center justify-center"
          >
            <div class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-violet-500/20 to-fuchsia-400/30 border border-violet-400/30 shadow-[0_18px_40px_rgba(139,92,246,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-violet-500" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">生成试卷</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  输入主题即可生成试卷，支持选择题、填空题、应用题（简答与计算），可基于备课资料、自定义题型数量与难度，生成后可直接查看题目与答案并导出 PDF。
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="px-4 py-2 rounded-full border border-violet-400/30 bg-white/80 text-sm text-slate-800 shadow-[0_8px_16px_rgba(15,23,42,0.08)] hover:bg-white transition-colors cursor-pointer"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-violet-500/15 text-violet-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">多题型组合</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">选择题、填空题、应用题（简答+计算）一次生成。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">备课资料可选</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可勾选备课资料夹，基于资料出题。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75v16.5m7.5-7.5h-15" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">难度可调</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">简单、中等、困难，默认中等。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-indigo-500/15 text-indigo-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15v10.5h-15z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">历史试卷</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">左侧可查看、打开、删除历史试卷。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-cyan-500/15 text-cyan-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">题型数量自定义</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">默认 10 选择、5 填空、5 应用题，可自定义。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-fuchsia-500/15 text-fuchsia-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25M3 12v9m0-9h18v-9H3Z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">PDF 导出</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">支持下载试卷与答案的 PDF。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <PaperTopicBar
                  :key="topicBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="() => start(topic)"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectDifficulty="setDifficulty"
                  :onSelectCounts="setCounts"
                  :includeMaterials="includeMaterials"
                  :difficulty="difficulty"
                  :countChoice="countChoice"
                  :countFill="countFill"
                  :countApplication="countApplication"
                  :isLoading="connecting"
                />
              </div>
            </div>
          </div>

          <div v-if="connecting" class="mt-10 space-y-4">
            <GenerationStatusCard
              emoji="📚"
              tone="violet"
              :title="paperWaitingTitle"
              description="系统正在组合题型、答案与解析，请稍候。"
              :phase="paperPhase"
              :steps="paperGenerationSteps"
            />

            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">当前任务</div>
                  <div class="mt-1 text-lg font-semibold text-[color:var(--app-text)]">{{ activePaperTopic }}</div>
                  <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span class="rounded-full border border-violet-300/60 bg-violet-100/80 px-2.5 py-1 font-semibold text-violet-800">
                      {{ currentPaperPhaseLabel }}
                    </span>
                    <span class="rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 px-2.5 py-1 text-[color:var(--nav-text-muted)]">
                      难度 {{ difficultyLabel }}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-4 py-2 text-sm font-medium text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]"
                  @click="newPaper"
                >
                  重新开始
                </button>
              </div>

              <div class="mt-4 grid gap-3 sm:grid-cols-3">
                <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                  <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">选择题</div>
                  <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">{{ countChoice }} 题</div>
                </div>
                <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                  <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">填空题</div>
                  <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">{{ countFill }} 题</div>
                </div>
                <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                  <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">应用题</div>
                  <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">{{ countApplication }} 题</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 生成完成后：题目与答案总览、按题型筛选、PDF 下载 -->
          <div v-if="questions.length > 0 && done" class="space-y-6">
            <div class="flex items-center justify-between flex-wrap gap-3">
              <h2 class="text-lg font-semibold text-[color:var(--app-text)]">题目与答案总览</h2>
              <div class="flex items-center gap-2 flex-wrap">
                <div class="flex rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 overflow-hidden">
                  <button
                    v-for="tab in typeTabs"
                    :key="tab.value"
                    type="button"
                    class="px-4 py-2 text-xs font-semibold transition-colors"
                    :class="filterType === tab.value ? 'bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)]' : 'text-[color:var(--nav-text-muted)] hover:bg-[color:var(--nav-hover-bg)]'"
                    @click="filterType = tab.value"
                  >
                    {{ tab.label }}
                  </button>
                </div>
                <a
                  :href="paperPdfUrl(paperId)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="download-pdf-btn px-4 py-2 rounded-2xl bg-rose-100 border-2 border-rose-400 text-rose-900 text-sm font-bold hover:bg-rose-200 transition-colors inline-flex items-center gap-2"
                >
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                  下载 PDF
                </a>
                <button
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors"
                  @click="newPaper"
                >
                  再出一份
                </button>
              </div>
            </div>
            <div class="space-y-8">
              <template v-for="group in questionsByType" :key="group.type">
                <div class="space-y-4">
                  <h3 class="text-lg font-bold text-[color:var(--app-text)] border-2 border-[color:var(--glass-border)] rounded-xl px-4 py-3 bg-[color:var(--nav-bg)]/60" style="font-family: 黑体, SimHei, sans-serif;">
                    {{ group.label }}
                  </h3>
                  <div
                    v-for="(item, i) in group.items"
                    :key="item.id"
                    class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]"
                  >
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-xs font-semibold text-[color:var(--nav-text-muted)]">第 {{ item.id }} 题</span>
                      <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-200" style="font-family: 黑体, SimHei, sans-serif;">{{ typeLabel(item.type) }}</span>
                    </div>
                    <div class="text-[color:var(--app-text)] font-medium mb-4">{{ item.question }}</div>
                    <!-- 选择题：选项 + 标出正确答案 -->
                    <div v-if="item.type === 'choice' && item.options?.length" class="space-y-2 mb-4">
                      <div
                        v-for="(opt, j) in item.options"
                        :key="j"
                        class="rounded-xl px-4 py-2.5 flex items-center gap-3"
                        :class="j === (item.correct ?? 1) - 1 ? 'bg-emerald-500/25 border-2 border-emerald-500/60 text-black' : 'bg-[color:var(--nav-bg)]/40 border border-[color:var(--nav-border)] text-[color:var(--app-text)]'"
                      >
                        <span class="w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold" :class="j === (item.correct ?? 1) - 1 ? 'border-emerald-600 text-black' : 'border-[color:var(--nav-border)]'">{{ String.fromCharCode(65 + j) }}</span>
                        <span :class="j === (item.correct ?? 1) - 1 ? 'font-medium text-black' : ''">{{ opt }}</span>
                        <span v-if="j === (item.correct ?? 1) - 1" class="ml-auto text-xs font-bold text-black">正确答案</span>
                      </div>
                    </div>
                    <!-- 填空题 / 应用题：参考答案 -->
                    <div v-if="item.type !== 'choice' && item.answer" class="mb-4 p-4 rounded-xl bg-sky-500/15 border-2 border-sky-400/50">
                      <div class="text-xs font-bold text-[color:var(--app-text)] mb-1">参考答案</div>
                      <div class="text-sm text-[color:var(--app-text)] whitespace-pre-wrap">{{ item.answer }}</div>
                    </div>
                    <div v-if="item.explanation" class="p-4 rounded-xl bg-amber-500/10 border border-amber-400/40">
                      <div class="text-xs font-bold text-[color:var(--app-text)] mb-2">解析</div>
                      <div class="text-sm text-[color:var(--app-text)] leading-relaxed">{{ item.explanation }}</div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { paperStart, connectPaperStream, getPaperDetail, paperPdfUrl, type PaperItem, type PaperEvent } from "../lib/api";
import { getUserScopedStorageKey, readScopedStorage } from "../lib/userStorage";
import { getRouteState } from "../lib/routerState";
import PaperTopicBar from "../components/Paper/PaperTopicBar.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import PaperHistoryPanel from "../components/Paper/PaperHistoryPanel.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

provide("learningFolderKey", computed(() => getUserScopedStorageKey("edumind-learning-folder-teacher")));
provide("chatRole", computed(() => "teacher"));
provide("chatBasePath", computed(() => "/teacher/chat"));
const paperListVersion = ref(0);
provide("paperListVersion", paperListVersion);

const route = useRoute();
const router = useRouter();
const topic = ref("");
const questions = ref<PaperItem[]>([]);
const paperId = ref("");
const connecting = ref(false);
const paperPhase = ref("generating");
const done = ref(false);
const includeMaterials = ref(false);
const difficulty = ref<"easy" | "medium" | "hard">("medium");
const countChoice = ref(10);
const countFill = ref(5);
const countApplication = ref(2);
const topicBarKey = ref(0);
const filterType = ref<"all" | "choice" | "fill" | "application">("all");
const closeRef = ref<null | (() => void)>(null);

const quickTopics = ["一元二次方程", "牛顿运动定律", "化学反应速率", "世界史大事件"];

const typeTabs = [
  { value: "all" as const, label: "全部" },
  { value: "choice" as const, label: "选择题" },
  { value: "fill" as const, label: "填空题" },
  { value: "application" as const, label: "应用题" },
];
const paperGenerationSteps = [
  { key: "generating", label: "正在出题" },
  { key: "packaging", label: "正在整理试卷" },
];
const paperWaitingTitle = computed(() =>
  paperPhase.value === "packaging" ? "试卷内容已经生成，正在整理版式" : "试卷正在生成",
);
const activePaperTopic = computed(() => topic.value.trim() || "未命名试卷");
const currentPaperPhaseLabel = computed(() => {
  const matched = paperGenerationSteps.find((item) => item.key === paperPhase.value);
  return matched?.label || "处理中";
});
const difficultyLabel = computed(() => {
  if (difficulty.value === "easy") return "简单";
  if (difficulty.value === "hard") return "困难";
  return "中等";
});

const filteredQuestions = computed(() => {
  if (filterType.value === "all") return questions.value;
  return questions.value.filter((q) => q.type === filterType.value);
});

/** 按题型分组的列表，用于展示题型标题：{ type, label, items }[] */
const questionsByType = computed(() => {
  const order: ("choice" | "fill" | "application")[] = ["choice", "fill", "application"];
  const labels: Record<string, string> = { choice: "选择题", fill: "填空题", application: "应用题" };
  const list = filterType.value === "all" ? questions.value : questions.value.filter((q) => q.type === filterType.value);
  const groups: { type: string; label: string; items: PaperItem[] }[] = [];
  for (const t of order) {
    const items = list.filter((q) => q.type === t);
    if (items.length) groups.push({ type: t, label: labels[t], items });
  }
  return groups;
});

function typeLabel(t: string) {
  if (t === "choice") return "选择题";
  if (t === "fill") return "填空题";
  if (t === "application") return "应用题";
  return t;
}

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("edumind-learning-folder-teacher"));

function loadLearningFolderIds(): string[] {
  try {
    const raw = readScopedStorage(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
}

function setTopic(v: string) {
  topic.value = v;
}

function setIncludeMaterials(v: boolean) {
  includeMaterials.value = v;
}

function setDifficulty(d: "easy" | "medium" | "hard") {
  difficulty.value = d;
}

function setCounts(c: { choice: number; fill: number; application: number }) {
  countChoice.value = c.choice;
  countFill.value = c.fill;
  countApplication.value = c.application;
}

function onQuickTopic(value: string) {
  if (connecting.value) return;
  topic.value = value;
  start(value);
}

async function start(t: string) {
  const trimmed = t.trim();
  if (!trimmed) return;
  if (closeRef.value) closeRef.value();

  questions.value = [];
  done.value = false;
  connecting.value = true;
  paperPhase.value = "generating";

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const s = await paperStart({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      difficulty: difficulty.value,
      count_choice: countChoice.value,
      count_fill: countFill.value,
      count_application: countApplication.value,
    });
    paperId.value = s.paperId;
    const { close } = connectPaperStream(s.paperId, (ev: PaperEvent) => {
      if (ev.type === "phase" && ev.value) {
        paperPhase.value = ev.value;
      }
      if (ev.type === "paper" && Array.isArray(ev.paper)) {
        paperPhase.value = "packaging";
        questions.value = ev.paper;
        connecting.value = false;
        done.value = true;
        paperListVersion.value++;
      }
      if (ev.type === "done" || ev.type === "error") connecting.value = false;
    });
    closeRef.value = close;
  } catch {
    connecting.value = false;
  }
}

async function loadPaper(id: string) {
  if (!id) return;
  try {
    const res = await getPaperDetail(id);
    if (res?.ok && Array.isArray(res.questions)) {
      questions.value = res.questions;
      topic.value = res.paper?.title ?? topic.value;
      paperId.value = id;
      done.value = true;
    }
  } catch {
    return;
  }
}

function newPaper() {
  if (closeRef.value) closeRef.value();
  questions.value = [];
  topic.value = "";
  paperId.value = "";
  connecting.value = false;
  paperPhase.value = "generating";
  done.value = false;
  filterType.value = "all";
  topicBarKey.value += 1;
}

const initialPaperId = (route.query.paperId as string) || getRouteState<{ paperId?: string }>().paperId || "";
const initialTopic = (route.query.topic as string) || getRouteState<{ topic?: string }>().topic || "";

onMounted(() => {
  if (initialPaperId) loadPaper(initialPaperId);
  else if (initialTopic) {
    topic.value = initialTopic;
    start(initialTopic);
  }
});

watch(
  () => route.query.paperId,
  async (next) => {
    const id = (next as string) || getRouteState<{ paperId?: string }>().paperId || "";
    if (!id) {
      if (closeRef.value) closeRef.value();
      newPaper();
      return;
    }
    if (id === paperId.value) return;
    await loadPaper(id);
  }
);

watch(
  () => route.query.new,
  () => {
    if (route.path === "/teacher/paper") {
      if (closeRef.value) closeRef.value();
      newPaper();
    }
  }
);

onBeforeUnmount(() => {
  if (closeRef.value) closeRef.value();
});
</script>

<style scoped>
.download-pdf-btn {
  font-family: "黑体", SimHei, "Microsoft YaHei", sans-serif;
  color: #881337;
}
.download-pdf-btn:hover {
  color: #9f1239;
}
</style>
