<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <QuizHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-semibold text-[color:var(--app-text)] flex items-center gap-3">{{ pageTitle }}</h1>
            </div>
          </div>

          <div v-if="qs.length === 0 && !done" class="min-h-[62vh] flex flex-col justify-center">
            <div v-if="!showQuizGeneratingView" class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-sky-500/20 to-cyan-400/30 border border-sky-400/30 shadow-[0_18px_40px_rgba(14,165,233,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-sky-500" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                    <circle cx="12" cy="12" r="9" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">{{ isTeacherPage ? '生成课堂测验' : '开始你的专属测验' }}</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  {{ isTeacherPage ? '输入主题即可生成测验题，生成后可查看全部题目、正确答案与解析，便于备课与课堂使用。' : '输入主题即可生成题目，系统会自动给出提示与解析，适合复习巩固与自测提升。' }}
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="px-4 py-2 rounded-full border border-sky-400/30 bg-white/80 text-sm text-slate-800 shadow-[0_8px_16px_rgba(15,23,42,0.08)] hover:bg-white transition-colors cursor-pointer"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15M4.5 12h10.5M4.5 17.25h7" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">题型结构清晰</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">题干、选项、提示与解析一目了然。</div>
                    </div>
                  </div>
                </div>
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12a7.5 7.5 0 1 1 15 0 7.5 7.5 0 0 1-15 0Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">即时反馈</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">作答后立即给出对错与解析。</div>
                    </div>
                  </div>
                </div>
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75v16.5m7.5-7.5h-15" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">难度可调</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">支持简单、中等、困难三种难度。</div>
                    </div>
                  </div>
                </div>
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-indigo-500/15 text-indigo-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15v10.5h-15z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75V4.5h7.5v2.25" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">历史可追溯</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">随时回看历史测验与作答情况。</div>
                    </div>
                  </div>
                </div>
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-cyan-500/15 text-cyan-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v9H5.25z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75v-1.5h7.5v1.5" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 15.75h7.5" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">资料驱动测验</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可基于上传资料生成更贴合的题目。</div>
                    </div>
                  </div>
                </div>
                <div :class="featureCardClass">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-fuchsia-500/15 text-fuchsia-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 5.25h10.5v13.5H6.75z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 8.25h6" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 15.75h6" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">题目数量可选</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">5/10/15 题灵活切换。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <TopicBar
                  :key="topicBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="() => start(topic)"
                  :isLoading="connecting"
                  :phase="connecting ? quizPhase : ''"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectCount="setQuestionCount"
                  :onSelectDifficulty="setDifficulty"
                  :countValue="questionCount"
                  :countOptions="[5, 10, 15]"
                  :difficultyValue="difficulty"
                  :materialsLabel="materialsLabel"
                />
              </div>
            </div>
            <div v-else class="w-full max-w-4xl mx-auto">
              <div class="relative overflow-hidden rounded-[32px] border border-sky-200/65 bg-white/96 p-6 md:p-8 shadow-[0_18px_42px_rgba(15,23,42,0.16)]">
                <div
                  class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.16),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(191,219,254,0.28),transparent_34%)]"
                  aria-hidden="true"
                />
                <div class="relative space-y-6">
                  <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div class="flex items-start gap-4">
                      <div class="flex size-16 shrink-0 items-center justify-center rounded-[24px] border border-sky-200/80 bg-white/90 text-sky-500 shadow-[0_14px_32px_rgba(14,165,233,0.16)]">
                        <div class="relative flex items-center justify-center">
                          <span class="absolute inline-flex size-10 rounded-full bg-sky-400/20 animate-ping" />
                          <svg viewBox="0 0 24 24" class="relative size-8" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                            <circle cx="12" cy="12" r="9" />
                          </svg>
                        </div>
                      </div>
                      <div>
                        <div class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600/80">{{ pageTitle }}</div>
                        <h2 class="mt-2 text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">{{ quizGeneratingTitle }}</h2>
                        <p class="mt-2 max-w-2xl text-sm md:text-base text-[color:var(--nav-text-muted)]">
                          {{ quizGeneratingDescription }}
                        </p>
                      </div>
                    </div>
                    <div class="rounded-2xl border border-sky-200/70 bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(14,165,233,0.12)]">
                      <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600/75">当前阶段</div>
                      <div class="mt-1 text-sm font-semibold text-slate-900">{{ currentQuizPhaseLabel }}</div>
                    </div>
                  </div>

                  <div class="flex flex-wrap gap-2">
                    <div
                      v-for="item in quizStatusMeta"
                      :key="item.label"
                      class="rounded-2xl border border-white/70 bg-white/80 px-3 py-2 shadow-[0_8px_18px_rgba(15,23,42,0.08)]"
                    >
                      <div class="text-[11px] font-semibold text-sky-700/70">{{ item.label }}</div>
                      <div class="max-w-[280px] truncate text-sm font-medium text-slate-900">{{ item.value }}</div>
                    </div>
                  </div>

                  <GenerationStatusCard
                    :emoji="isTeacherPage ? '🧪' : '📝'"
                    :tone="isTeacherPage ? 'sky' : 'amber'"
                    :title="quizGeneratingTitle"
                    :description="quizGeneratingDescription"
                    :phase="quizCardPhase"
                    :steps="quizGenerationSteps"
                  />

                  <div class="grid gap-3 sm:grid-cols-3">
                    <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/70 p-4">
                      <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">当前主题</div>
                      <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">{{ activeQuizTopic }}</div>
                    </div>
                    <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/70 p-4">
                      <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">完成后</div>
                      <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">
                        {{ isTeacherPage ? '会直接展示整份题目、答案与解析。' : '会直接进入答题流程。' }}
                      </div>
                    </div>
                    <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/70 p-4">
                      <div class="text-xs font-semibold text-[color:var(--nav-text-muted)]">当前状态</div>
                      <div class="mt-2 text-sm font-medium text-[color:var(--app-text)]">{{ waitingStatusMessage }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

      <!-- 教师端：生成完成后直接展示全部题目与答案、解析 -->
      <div v-if="isTeacherPage && qs.length > 0" class="space-y-6">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <h2 class="text-lg font-semibold text-[color:var(--app-text)]">题目与答案总览</h2>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors"
              @click="newTopic"
            >
              再出一份
            </button>
          </div>
        </div>
        <div class="space-y-6">
          <div
            v-for="(item, i) in qs"
            :key="item.id"
            class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]"
          >
            <div class="text-xs font-semibold text-[color:var(--nav-text-muted)] mb-2">第 {{ i + 1 }} 题</div>
            <div class="text-[color:var(--app-text)] font-medium mb-4">{{ item.question }}</div>
            <div class="space-y-2 mb-4">
              <div
                v-for="(opt, j) in item.options"
                :key="j"
                class="rounded-xl px-4 py-2.5 flex items-center gap-3"
                :class="j === item.correct ? 'bg-emerald-500/25 border-2 border-emerald-500/60 text-[color:var(--app-text)]' : 'bg-[color:var(--nav-bg)]/40 border border-[color:var(--nav-border)] text-[color:var(--app-text)]'"
              >
                <span class="w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold" :class="j === item.correct ? 'border-emerald-600 text-[color:var(--app-text)]' : 'border-[color:var(--nav-border)]'">{{ String.fromCharCode(65 + j) }}</span>
                <span :class="j === item.correct ? 'font-medium text-[color:var(--app-text)]' : ''">{{ opt }}</span>
                <span v-if="j === item.correct" class="ml-auto text-xs font-bold text-[color:var(--app-text)]">正确答案</span>
              </div>
            </div>
            <div v-if="item.hint" class="mb-3 p-3 rounded-xl bg-amber-400/15 border border-amber-400/40">
              <div class="text-xs font-bold text-[color:var(--app-text)] mb-1">提示</div>
              <div class="text-sm text-[color:var(--nav-text-muted)]">{{ item.hint }}</div>
            </div>
            <div v-if="item.explanation" class="p-4 rounded-xl bg-sky-500/15 border-2 border-sky-400/50 shadow-[0_4px_14px_rgba(14,165,233,0.2)]">
              <div class="text-xs font-bold text-[color:var(--app-text)] mb-2">解析</div>
              <div class="text-sm text-[color:var(--app-text)] leading-relaxed">{{ item.explanation }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="qs.length > 0 && !done && q">
        <QuizHeader
          :topic="topic || 'Quiz'"
          :idx="idx"
          :total="total"
          :score="score"
          :status="questionStatus"
          :onJump="jumpTo"
        />
        <QuestionCard
          :q="q"
          :selected="selected"
          :showExp="showExp"
          :showHint="showHint"
          :onSelect="onSelect"
          :onHint="onHint"
          :onSubmit="onSubmit"
          :onNext="onNext"
          :isLast="idx === total - 1"
        />
      </div>

      <ResultsPanel
        v-if="done && !isTeacherPage"
        :score="score"
        :total="total"
        :percentage="percentage"
        :visual="resultVisual"
        :answers="answers"
        :onRetake="onRetake"
        :onReview="() => openReviewAt(null)"
        :onNewTopic="newTopic"
        :onReviewQuestion="openReviewAt"
      />

          <ReviewModal
            v-if="reviewOpen && !isTeacherPage"
            :answers="answers"
            :initialIndex="reviewTarget"
            :onClose="closeReview"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  quizStart,
  connectQuizStream,
  friendlyTaskMessage,
  getQuizDetail,
  saveQuizAttempts,
  err as apiErr,
  type QuizEvent,
  type QuizMeta,
  type QuizRecordStatus,
} from "../lib/api";
import { getUserScopedStorageKey, readScopedStorage } from "../lib/userStorage";
import TopicBar from "../components/Quiz/TopicBar.vue";
import QuizHeader from "../components/Quiz/QuizHeader.vue";
import QuestionCard from "../components/Quiz/QuestionCard.vue";
import ResultsPanel from "../components/Quiz/ResultsPanel.vue";
import ReviewModal from "../components/Quiz/ReviewModal.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import QuizHistoryPanel from "../components/Quiz/QuizHistoryPanel.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

export type Question = {
  id: number;
  question: string;
  options: string[];
  correct: number;
  hint: string;
  explanation: string;
  imageHtml?: string;
};
export type UA = {
  questionId: number;
  selectedAnswer: number;
  correct: boolean;
  question: string;
  selectedOption: string;
  correctOption: string;
  explanation: string;
  at?: number;
};

type Visual = { msg: string; cls: string; icon: "trophy" | "spark" | "book" | "bolt" };
type QuizHistoryUpdateDetail = {
  quizId?: string;
  role?: "student" | "teacher";
  title?: string;
  count?: number;
  status?: QuizRecordStatus;
  at?: number;
};

const route = useRoute();
const router = useRouter();

const isTeacherPage = computed(() => route.path.startsWith("/teacher/"));
const pageTitle = computed(() => (isTeacherPage.value ? "课堂测验" : "测验"));
const materialsLabel = computed(() => (isTeacherPage.value ? "备课资料" : "学习资料"));
const quizGeneratingTitle = computed(() => (isTeacherPage.value ? "课堂测验正在生成" : "专属测验正在生成"));
const quizGeneratingDescription = computed(() =>
  isTeacherPage.value
    ? "系统已经收到你的主题，正在组织题干、选项、答案和解析，完成后会自动展示整份课堂测验。"
    : "系统已经收到你的主题，正在整理题目、提示和解析，完成后会自动进入答题流程。"
);

const featureCardClass = computed(() =>
  isTeacherPage.value
    ? "rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]"
    : "rounded-3xl border border-amber-200/60 dark:border-amber-800/50 bg-gradient-to-br from-amber-50 to-yellow-50/90 dark:from-amber-950/50 dark:to-yellow-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]"
);

provide("quizRole", computed(() => (isTeacherPage.value ? "teacher" : "student")));
provide("quizBasePath", computed(() => (isTeacherPage.value ? "/teacher/quiz" : "/quiz")));
const learningFolderKeyComputed = computed(() =>
  getUserScopedStorageKey(isTeacherPage.value ? "edumind-learning-folder-teacher" : "edumind-learning-folder")
);
provide("learningFolderKey", learningFolderKeyComputed);
provide("chatRole", computed(() => (isTeacherPage.value ? "teacher" : "student")));
provide("chatBasePath", computed(() => (isTeacherPage.value ? "/teacher/chat" : "/chat")));

const isExplicitNewRoute = computed(() => route.query.new != null);
const initialTopic = (route.query.topic as string) || "";
const initialQuizId = (route.query.quizId as string) || "";

const topic = ref(initialTopic);
const qs = ref<Question[]>([]);
const quizId = ref(initialQuizId);
const idx = ref(0);
const score = ref(0);
const selections = ref<Array<number | null>>([]);
const hintShown = ref<boolean[]>([]);
const expShown = ref<boolean[]>([]);
const done = ref(false);
const answers = ref<UA[]>([]);
const reviewOpen = ref(false);
const reviewTarget = ref<number | null>(null);
const connecting = ref(false);
const quizStatus = ref<QuizRecordStatus | "idle">("idle");
const quizPhase = ref("generating");
const generateError = ref("");
const includeMaterials = ref(false);
const questionCount = ref(5);
const difficulty = ref<"easy" | "medium" | "hard">("medium");
const topicBarKey = ref(0);
const quickTopics = [
  "一次函数",
  "牛顿运动定律",
  "化学反应速率",
  "世界史大事件",
];
const difficultyLabels: Record<"easy" | "medium" | "hard", string> = {
  easy: "简单",
  medium: "中等",
  hard: "困难",
};
const quizGenerationSteps = [
  { key: "generating", label: "正在生成题目" },
  { key: "packaging", label: "正在整理答案" },
  { key: "done", label: "正在准备展示" },
];

const normalizeQuizStatus = (status?: string): QuizRecordStatus => {
  if (status === "ready" || status === "generating" || status === "packaging" || status === "error") return status;
  return "pending";
};

const isQuizPendingStatus = (status?: string) => {
  const normalized = normalizeQuizStatus(status);
  return normalized === "pending" || normalized === "generating" || normalized === "packaging";
};

const LEARNING_FOLDER_KEY = computed(() =>
  getUserScopedStorageKey(isTeacherPage.value ? "edumind-learning-folder-teacher" : "edumind-learning-folder")
);
const QUIZ_ATTEMPTS_KEY = computed(() => getUserScopedStorageKey("quiz:attempts"));

const closeRef = ref<null | (() => void)>(null);
const activeRunToken = ref(0);

const beginQuizRun = () => {
  activeRunToken.value += 1;
  return activeRunToken.value;
};

const isCurrentRun = (token: number) => token === activeRunToken.value;

const notifyHistoryUpdated = (nextQuizId?: string, detail: Omit<QuizHistoryUpdateDetail, "quizId" | "role"> = {}) => {
  try {
    window.dispatchEvent(
      new CustomEvent("quiz:updated", {
        detail: {
          quizId: nextQuizId || quizId.value,
          role: isTeacherPage.value ? "teacher" : "student",
          ...detail,
        } satisfies QuizHistoryUpdateDetail,
      })
    );
  } catch {
    return;
  }
};

const applyQuizMeta = (meta?: QuizMeta | null) => {
  if (!meta) return;
  if (meta.title) topic.value = meta.title;
  if (typeof meta.count === "number" && meta.count > 0) questionCount.value = meta.count;
  if (meta.difficulty === "easy" || meta.difficulty === "medium" || meta.difficulty === "hard") {
    difficulty.value = meta.difficulty;
  }
  if (typeof meta.includeMaterials === "boolean") {
    includeMaterials.value = meta.includeMaterials;
  }
  quizStatus.value = normalizeQuizStatus(meta.status);
};

const applyQuizQuestions = (items: Question[]) => {
  const arr = items.map((item) => ({
    ...item,
    correct: typeof item.correct === "number" ? Math.max(0, item.correct - 1) : 0,
  }));
  qs.value = arr;
  idx.value = 0;
  initQuestionState(arr.length);
  done.value = false;
  generateError.value = "";
  quizStatus.value = "ready";
  connecting.value = false;
  return arr;
};

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

const waitForQuizResult = async (qid: string, fallbackTitle: string, token: number) => {
  let attempt = 0;
  while (isCurrentRun(token)) {
    if (quizId.value !== qid) return false;
    try {
      const res = await getQuizDetail(qid);
      if (!isCurrentRun(token) || quizId.value !== qid) return false;
      applyQuizMeta(res?.quiz);
      if (Array.isArray(res?.questions) && res.questions.length) {
        const arr = applyQuizQuestions(res.questions);
        notifyHistoryUpdated(qid, {
          title: res.quiz?.title || fallbackTitle,
          count: arr.length || questionCount.value,
          status: "ready",
          at: Date.now(),
        });
        return true;
      }
      connecting.value = true;
    } catch {
      if (!isCurrentRun(token) || quizId.value !== qid) return false;
    }
    attempt += 1;
    await wait(attempt <= 8 ? 500 : attempt <= 20 ? 1500 : 3000);
  }
  return false;
};

const total = computed(() => qs.value.length);
const q = computed(() => qs.value[idx.value]);
const selected = computed(() => selections.value[idx.value] ?? null);
const showHint = computed(() => hintShown.value[idx.value] ?? false);
const showExp = computed(() => expShown.value[idx.value] ?? false);
const hasSubmittedQuizRequest = computed(() => Boolean(quizId.value));
const showQuizGeneratingView = computed(
  () => hasSubmittedQuizRequest.value && qs.value.length === 0 && !done.value
);
const activeQuizTopic = computed(() => topic.value.trim() || "未命名主题");
const quizCardPhase = computed(() => (quizPhase.value === "packaging" || quizStatus.value === "packaging" ? "packaging" : "generating"));
const currentQuizPhaseLabel = computed(() => {
  if (quizStatus.value === "pending") return "等待开始";
  if (quizStatus.value === "error") return "等待结果返回";
  return quizGenerationSteps.find((step) => step.key === quizCardPhase.value)?.label || "正在处理中";
});
const quizStatusMeta = computed(() => [
  { label: "主题", value: activeQuizTopic.value },
  { label: "题目数量", value: `${questionCount.value} 题` },
  { label: "难度", value: difficultyLabels[difficulty.value] },
  { label: materialsLabel.value, value: includeMaterials.value ? "已启用" : "未启用" },
]);
const waitingStatusMessage = computed(() => {
  if (quizCardPhase.value === "packaging") {
    return "题目已经生成，正在整理答案与解析，完成后会自动展示。";
  }
  if (generateError.value) {
    return "结果还在返回中，页面会继续自动刷新，请稍候。";
  }
  if (quizStatus.value === "pending") {
    return "请求已经提交，系统正在排队启动生成。";
  }
  return "请求已经提交，无需重复点击，结果会自动出现。";
});
const questionStatus = computed(() =>
  qs.value.map((item) => {
    const hit = answers.value.find((a) => a.questionId === item.id);
    if (!hit) return "unanswered" as const;
    return hit.correct ? ("correct" as const) : ("wrong" as const);
  })
);

const percentage = computed(() => (total.value ? Math.round((score.value / total.value) * 100) : 0));

const resultVisual = computed<Visual>(() => {
  if (percentage.value >= 90)
    return { msg: "太棒了！你已经掌握了这个主题！", cls: "bg-emerald-500/12 border border-emerald-500/36", icon: "trophy" };
  if (percentage.value >= 70)
    return { msg: "做得好！你有扎实的理解。", cls: "bg-sky-500/12 border border-sky-500/36", icon: "spark" };
  if (percentage.value >= 50)
    return { msg: "不错！复习一下概念再试一次吧。", cls: "bg-amber-500/12 border border-amber-500/36", icon: "book" };
  return { msg: "继续加油！熟能生巧。", cls: "bg-rose-500/12 border border-rose-500/36", icon: "bolt" };
});

const setTopic = (v: string) => {
  topic.value = v;
};

const onQuickTopic = (value: string) => {
  if (connecting.value) return;
  topic.value = value;
  start(value);
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const setQuestionCount = (next: number) => {
  questionCount.value = next;
};

const setDifficulty = (next: "easy" | "medium" | "hard") => {
  difficulty.value = next;
};

const loadLearningFolderIds = () => {
  try {
    const key = LEARNING_FOLDER_KEY.value;
    const raw = localStorage.getItem(key);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [] as string[];
  }
};

const initQuestionState = (count: number) => {
  selections.value = Array(count).fill(null);
  hintShown.value = Array(count).fill(false);
  expShown.value = Array(count).fill(false);
};

const resetQuestionState = () => {
  idx.value = 0;
  initQuestionState(total.value || 0);
};

const takeQuizArray = (a: unknown): Question[] => {
  if (Array.isArray(a)) return a as Question[];
  if (Array.isArray((a as any)?.quiz)) return (a as any).quiz as Question[];
  return [];
};

const normalizeQuizError = (raw?: string) => {
  return friendlyTaskMessage(raw, {
    feature: "quiz",
    fallback: "这次测验还没有顺利准备好，请稍后再试。",
  });
};

const resetQuizComposerState = () => {
  if (closeRef.value) {
    closeRef.value();
    closeRef.value = null;
  }
  beginQuizRun();
  connecting.value = false;
  done.value = false;
  qs.value = [];
  topic.value = "";
  quizId.value = "";
  answers.value = [];
  initQuestionState(0);
  score.value = 0;
  quizStatus.value = "idle";
  quizPhase.value = "generating";
  includeMaterials.value = false;
  difficulty.value = "medium";
  generateError.value = "";
  reviewOpen.value = false;
  reviewTarget.value = null;
  topicBarKey.value += 1;
};

const start = async (t: string) => {
  const trimmed = t.trim();
  if (!trimmed) return;
  if (closeRef.value) {
    closeRef.value();
    closeRef.value = null;
  }
  const runToken = beginQuizRun();

  qs.value = [];
  initQuestionState(0);
  score.value = 0;
  done.value = false;
  answers.value = [];
  generateError.value = "";
  connecting.value = true;
  quizStatus.value = "pending";
  quizPhase.value = "generating";

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const s = await quizStart({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      count: questionCount.value,
      difficulty: difficulty.value,
      role: isTeacherPage.value ? "teacher" : "student",
    });
    if (!isCurrentRun(runToken)) return;
    quizId.value = s.quizId;
    notifyHistoryUpdated(s.quizId, {
      title: trimmed,
      count: questionCount.value,
      status: "pending",
      at: Date.now(),
    });
    let completed = false;
    let finishing = false;
    const { close } = connectQuizStream(s.quizId, (ev: QuizEvent) => {
      if (!isCurrentRun(runToken)) {
        close();
        if (closeRef.value === close) closeRef.value = null;
        return;
      }
      if (ev.type === "phase" && ev.value) {
        quizPhase.value = ev.value;
        quizStatus.value = ev.value === "packaging" ? "packaging" : "generating";
        notifyHistoryUpdated(s.quizId, {
          title: trimmed,
          count: questionCount.value,
          status: quizStatus.value,
          at: Date.now(),
        });
        return;
      }
      if (ev.type === "quiz") {
        quizPhase.value = "packaging";
        const arr = applyQuizQuestions(takeQuizArray(ev.quiz));
        connecting.value = false;
        completed = true;
        finishing = false;
        generateError.value = "";
        notifyHistoryUpdated(s.quizId, {
          title: trimmed,
          count: arr.length || questionCount.value,
          status: "ready",
          at: Date.now(),
        });
        close();
        closeRef.value = null;
        return;
      }
      if (ev.type === "done") {
        finishing = true;
        if (!completed) {
          void waitForQuizResult(s.quizId, trimmed, runToken).finally(() => {
            completed = true;
            close();
            if (closeRef.value === close) closeRef.value = null;
          });
          return;
        }
        quizPhase.value = "done";
        return;
      }
      if (ev.type === "error") {
        if (completed || finishing) return;
        generateError.value = normalizeQuizError(ev.error);
        close();
        if (closeRef.value === close) closeRef.value = null;
        void waitForQuizResult(s.quizId, trimmed, runToken);
        return;
      }
    });
    if (!isCurrentRun(runToken)) {
      close();
      return;
    }
    closeRef.value = close;

    const quizPath = isTeacherPage.value ? "/teacher/quiz" : "/quiz";
    if (route.query.topic !== trimmed || route.query.quizId !== s.quizId) {
      router.replace({ path: quizPath, query: { topic: trimmed, quizId: s.quizId }, state: { topic: trimmed, quizId: s.quizId } });
    }
  } catch (e) {
    if (!isCurrentRun(runToken)) return;
    connecting.value = false;
    quizStatus.value = "idle";
    generateError.value = apiErr(e);
  }
};

const loadQuiz = async (qid: string) => {
  if (!qid) return;
  const runToken = beginQuizRun();
  try {
    const res = await getQuizDetail(qid);
    if (!isCurrentRun(runToken)) return;
    if (res?.ok && Array.isArray(res.questions)) {
      applyQuizMeta(res.quiz);
      quizId.value = qid;
      done.value = false;
      generateError.value = "";
      if (res.questions.length > 0) {
        const arr = applyQuizQuestions(res.questions);
        notifyHistoryUpdated(qid, {
          title: res.quiz?.title || topic.value,
          count: arr.length || questionCount.value,
          status: "ready",
          at: Date.now(),
        });
      } else {
        qs.value = [];
        connecting.value = true;
        if (!closeRef.value) {
          void waitForQuizResult(qid, res.quiz?.title || topic.value, runToken);
        }
      }
    }
  } catch {
    return;
  }
};

const onSelect = (i: number) => {
  if (showExp.value) return;
  selections.value[idx.value] = i;
};

const onHint = () => {
  hintShown.value[idx.value] = true;
};

const onSubmit = () => {
  if (selected.value == null || !q.value || showExp.value) return;
  const correct = selected.value === q.value.correct;
  const ua: UA = {
    questionId: q.value.id,
    selectedAnswer: selected.value,
    correct,
    question: q.value.question,
    selectedOption: q.value.options[selected.value],
    correctOption: q.value.options[q.value.correct],
    explanation: q.value.explanation,
    at: Date.now(),
  };
  answers.value = [...answers.value, ua];
  expShown.value[idx.value] = true;
  if (correct) score.value += 1;
  saveAttempt();
};

const onNext = () => {
  if (!showExp.value) return;
  if (idx.value === total.value - 1) {
    done.value = true;
    saveAttempt();
    return;
  }
  idx.value += 1;
};

const jumpTo = (next: number) => {
  if (next < 0 || next >= total.value) return;
  idx.value = next;
};

const onRetake = () => {
  resetQuestionState();
  score.value = 0;
  done.value = false;
  answers.value = [];
};

const newTopic = () => {
  resetQuizComposerState();
  const quizPath = isTeacherPage.value ? "/teacher/quiz" : "/quiz";
  if (route.query.quizId || route.query.topic) {
    void router.replace({ path: quizPath, query: { new: String(Date.now()) }, state: { topic: "", quizId: "" } });
  }
};

const saveAttempt = () => {
  if (!quizId.value || !answers.value.length) return;
  try {
    const raw = localStorage.getItem(QUIZ_ATTEMPTS_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as Record<string, UA[]>) : {};
    parsed[quizId.value] = answers.value;
    localStorage.setItem(QUIZ_ATTEMPTS_KEY.value, JSON.stringify(parsed));
    void saveQuizAttempts(quizId.value, answers.value).catch(() => {});
  } catch {
    return;
  }
};

const openReviewAt = (index: number | null) => {
  reviewTarget.value = index;
  reviewOpen.value = true;
};

const closeReview = () => {
  reviewOpen.value = false;
  reviewTarget.value = null;
};

onMounted(() => {
  if (isExplicitNewRoute.value) {
    resetQuizComposerState();
    return;
  }
  if (initialQuizId) loadQuiz(initialQuizId);
  else if (initialTopic) topic.value = initialTopic;
});

watch(
  () => route.query.quizId,
  async (next) => {
    const qid = (next as string) || "";
    if (!qid) {
      resetQuizComposerState();
      return;
    }
    if (qid === quizId.value) return;
    await loadQuiz(qid);
  }
);

watch(
  () => route.query.new,
  (next) => {
    if (next && (route.path === "/quiz" || route.path === "/teacher/quiz")) {
      resetQuizComposerState();
    }
  }
);

watch(
  () => route.query.topic,
  (next) => {
    if (quizId.value) return;
    topic.value = typeof next === "string" ? next : "";
  }
);

onBeforeUnmount(() => {
  beginQuizRun();
  if (closeRef.value) closeRef.value();
});
</script>
