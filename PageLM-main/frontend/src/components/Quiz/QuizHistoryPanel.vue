<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" />
          </svg>
        </span>
        历史测验
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewQuiz"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建测验
      </button>
    </div>
    <div v-if="loading && !quizzes.length" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="quizzes.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="quiz in quizzes" :key="quiz.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] border transition-colors"
            :class="quizButtonClass(quiz)"
            @click="openQuiz(quiz.id)"
            @contextmenu.prevent="openContextMenu($event, quiz)"
            :title="quiz.title || '未命名测验'"
          >
            <div class="flex items-start gap-2">
              <div class="min-w-0 flex-1 truncate">{{ quiz.title || "未命名测验" }}</div>
              <span
                class="shrink-0 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold"
                :class="quizStatusChipClass(quiz.status)"
              >
                <span
                  class="inline-flex size-1.5 rounded-full bg-current"
                  :class="isQuizPending(quiz.status) ? 'animate-pulse' : ''"
                />
                {{ quizStatusLabel(quiz.status) }}
              </span>
            </div>
            <div class="mt-1 flex items-center gap-2 text-[10px] text-[color:var(--nav-text-muted)]">
              <span>题目数量：{{ quiz.count || 5 }}</span>
              <span v-if="isQuizPending(quiz.status)">系统正在生成中</span>
              <span v-else-if="quiz.status === 'error'" class="text-rose-400">生成失败</span>
            </div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            :class="!isQuizReady(quiz.status) ? 'opacity-70' : ''"
            @click.stop="toggleDetails(quiz)"
            :aria-label="isQuizReady(quiz.status) ? '查看测验详情' : '查看生成状态'"
            :title="isQuizReady(quiz.status) ? '查看测验详情' : '查看生成状态'"
          >
            <svg v-if="isQuizReady(quiz.status)" viewBox="0 0 24 24" class="size-4 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" class="size-4 text-amber-300 animate-spin" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75A8.25 8.25 0 1 0 20.25 12" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removeQuiz(quiz.id)"
            aria-label="删除测验"
            :title="'删除测验'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
        <div v-if="expandedId === quiz.id" class="mt-3 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-3">
          <div v-if="!isQuizReady(quiz.status)" class="rounded-2xl border border-amber-300/40 bg-amber-400/10 p-3 text-xs text-[color:var(--app-text)]">
            <div class="font-semibold">{{ quizStatusLabel(quiz.status) }}</div>
            <div class="mt-1 text-[color:var(--nav-text-muted)]">这份测验还在生成中，右侧主页面会持续展示生成进度，完成后会自动更新。</div>
          </div>
          <div v-else-if="details[quiz.id]?.length" class="relative">
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs text-[color:var(--nav-text-muted)]">题目与答案</span>
              <div class="flex items-center gap-1">
                <button
                  type="button"
                  class="p-1.5 rounded-lg bg-[color:var(--nav-bg)]/80 border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)] transition-colors"
                  aria-label="向上滑动"
                  @click="scrollDetailUp(quiz.id)"
                >
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-1.5 rounded-lg bg-[color:var(--nav-bg)]/80 border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)] transition-colors"
                  aria-label="向下滑动"
                  @click="scrollDetailDown(quiz.id)"
                >
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>
            <div
              :ref="(el) => setDetailRef(quiz.id, el)"
              class="space-y-3 max-h-64 overflow-y-auto overflow-x-hidden custom-scroll pr-1"
            >
              <div v-for="(item, i) in details[quiz.id]" :key="item.id" class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-3">
                <div class="text-xs text-[color:var(--nav-text-muted)]">第 {{ i + 1 }} 题</div>
                <div class="mt-1 text-sm text-[color:var(--app-text)]">{{ item.question }}</div>
                <div class="mt-2 text-xs text-emerald-300">答案：{{ correctAnswer(item) }}</div>
              </div>
            </div>
          </div>
          <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无测验详情</div>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史测验</div>
    <HistoryContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="closeContextMenu"
      @select="addQuizToBag"
    />
  </aside>
</template>

<script setup lang="ts">
import { type Ref, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deleteQuiz, getQuizDetail, listQuizzes, type QuizMeta, type QuizRecordStatus } from "../../lib/api";
import { addLearningBagRecord } from "../../lib/learningBag";
import HistoryContextMenu from "../common/HistoryContextMenu.vue";

const router = useRouter();
const route = useRoute();
const quizRole = inject<Ref<"student" | "teacher">>("quizRole");
const quizBasePath = inject<Ref<string>>("quizBasePath");
const loading = ref(false);
const quizzes = ref<QuizMeta[]>([]);
const expandedId = ref<string | null>(null);
const details = ref<Record<string, { id: number; question: string; options: string[]; correct: number }[]>>({});
const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextTarget = ref<QuizMeta | null>(null);
const detailScrollRefs = ref<Record<string, HTMLElement | null>>({});

type QuizUpdatedDetail = {
  quizId?: string;
  role?: "student" | "teacher";
  title?: string;
  count?: number;
  status?: QuizRecordStatus;
  at?: number;
  remove?: boolean;
};

const normalizeQuizStatus = (status?: string): QuizRecordStatus => {
  if (status === "ready" || status === "generating" || status === "packaging" || status === "error") return status;
  return "pending";
};

const isQuizPending = (status?: string) => {
  const normalized = normalizeQuizStatus(status);
  return normalized === "pending" || normalized === "generating" || normalized === "packaging";
};

const isQuizReady = (status?: string) => normalizeQuizStatus(status) === "ready";

const quizStatusLabel = (status?: string) => {
  const normalized = normalizeQuizStatus(status);
  if (normalized === "generating") return "生成中";
  if (normalized === "packaging") return "整理中";
  if (normalized === "ready") return "已完成";
  if (normalized === "error") return "失败";
  return "等待中";
};

const quizStatusChipClass = (status?: string) => {
  const normalized = normalizeQuizStatus(status);
  if (normalized === "ready") return "border-emerald-300/70 bg-emerald-400/15 text-emerald-300";
  if (normalized === "error") return "border-rose-300/70 bg-rose-400/15 text-rose-300";
  return "border-sky-300/70 bg-sky-400/15 text-sky-300";
};

const quizButtonClass = (quiz: QuizMeta) => {
  if (isQuizPending(quiz.status)) return "border-sky-300/60 bg-sky-400/10 hover:bg-sky-400/15";
  if (normalizeQuizStatus(quiz.status) === "error") return "border-rose-300/50 bg-rose-400/10 hover:bg-rose-400/15";
  return "bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border-[color:var(--nav-border)]";
};

const sortQuizzes = (items: QuizMeta[]) => {
  return [...items].sort((a, b) => Number(b.at || 0) - Number(a.at || 0));
};

const upsertQuiz = (quiz: QuizMeta) => {
  const normalized: QuizMeta = { ...quiz, status: normalizeQuizStatus(quiz.status), at: quiz.at || Date.now() };
  const next = quizzes.value.filter((item) => item.id !== normalized.id);
  quizzes.value = sortQuizzes([normalized, ...next]);
};

const setDetailRef = (id: string, el: unknown) => {
  if (el && typeof (el as HTMLElement).scrollBy === "function") {
    detailScrollRefs.value[id] = el as HTMLElement;
  } else {
    detailScrollRefs.value[id] = null;
  }
};

const scrollDetailUp = (id: string) => {
  const el = detailScrollRefs.value[id];
  if (el) el.scrollBy({ top: -120, behavior: "smooth" });
};

const scrollDetailDown = (id: string) => {
  const el = detailScrollRefs.value[id];
  if (el) el.scrollBy({ top: 120, behavior: "smooth" });
};

const role = () => quizRole?.value ?? "student";
const basePath = () => quizBasePath?.value ?? "/quiz";

const loadQuizzes = async () => {
  loading.value = true;
  try {
    const res = await listQuizzes(role());
    quizzes.value = Array.isArray(res?.quizzes)
      ? sortQuizzes(res.quizzes.map((quiz) => ({ ...quiz, status: normalizeQuizStatus(quiz.status) })))
      : [];
  } catch {
    quizzes.value = [];
  } finally {
    loading.value = false;
  }
};

const openQuiz = (id: string) => {
  if (!id) return;
  const currentId = route.query.quizId as string;
  if (currentId === id) {
    router.replace({ path: basePath() }).then(() => {
      router.push({ path: basePath(), query: { quizId: id, t: String(Date.now()) }, state: { quizId: id } });
    });
    return;
  }
  router.push({ path: basePath(), query: { quizId: id, t: String(Date.now()) }, state: { quizId: id } });
};

const startNewQuiz = () => {
  router.push({ path: basePath(), query: { new: String(Date.now()) }, state: { topic: "", quizId: "" } });
};

const openContextMenu = (event: MouseEvent, quiz: QuizMeta) => {
  contextTarget.value = quiz;
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

const addQuizToBag = () => {
  const quiz = contextTarget.value;
  if (!quiz?.id) return;
  addLearningBagRecord({
    type: "quiz",
    refId: quiz.id,
    title: quiz.title || "未命名测验",
    subtitle: `题目数量：${quiz.count || 5}`,
    path: basePath(),
    query: { quizId: quiz.id },
  });
};

const toggleDetails = async (quiz: QuizMeta) => {
  const id = quiz.id;
  if (!id) return;
  if (!isQuizReady(quiz.status)) {
    openQuiz(id);
    expandedId.value = id;
    return;
  }
  if (expandedId.value === id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = id;
  if (!details.value[id]) {
    try {
      const res = await getQuizDetail(id);
      if (res?.ok && Array.isArray(res.questions)) {
        details.value = { ...details.value, [id]: res.questions };
      }
    } catch {
      return;
    }
  }
};

const correctAnswer = (item: { options: string[]; correct: number }) => {
  const idx = Math.max(0, (item.correct || 1) - 1);
  return item.options[idx] || "";
};

const removeQuiz = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该测验吗？");
  if (!ok) return;
  const prev = quizzes.value;
  quizzes.value = prev.filter((item) => item.id !== id);
  try {
    await deleteQuiz(id);
    if ((route.query.quizId as string) === id) {
      router.push({ path: basePath() });
    }
    await loadQuizzes();
  } catch {
    quizzes.value = prev;
  }
};

onMounted(loadQuizzes);
watch(() => quizRole?.value, () => loadQuizzes());

const onQuizUpdated = (event: Event) => {
  const detail = (event as CustomEvent<QuizUpdatedDetail>).detail;
  if (!detail?.role || detail.role === role()) {
    if (detail.remove && detail.quizId) {
      quizzes.value = quizzes.value.filter((item) => item.id !== detail.quizId);
      return;
    }
    if (detail.quizId) {
      const prev = quizzes.value.find((item) => item.id === detail.quizId);
      upsertQuiz({
        id: detail.quizId,
        title: detail.title ?? prev?.title,
        count: detail.count ?? prev?.count,
        at: detail.at ?? Date.now(),
        status: detail.status ?? prev?.status ?? "pending",
      });
    }
    void loadQuizzes();
  }
};

onMounted(() => {
  window.addEventListener("quiz:updated", onQuizUpdated as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("quiz:updated", onQuizUpdated as EventListener);
});
</script>
