<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <LessonPlanHistoryPanel ref="historyRef" class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">教案生成</h1>
          </div>

          <!-- 空状态：未生成且未选择历史 -->
          <div
            v-if="!plan && !loading"
            class="min-h-[62vh] flex flex-col items-center justify-center"
          >
            <div class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-amber-500/20 to-orange-400/30 border border-amber-400/30 shadow-[0_18px_40px_rgba(245,158,11,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-amber-500" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">生成标准教案</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  输入课题即可生成包含三维目标、重难点、教学准备、教学过程与作业设计的规范教案，可选用备课资料辅助生成。
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="px-4 py-2 rounded-full border border-amber-400/30 bg-white/80 dark:bg-[color:var(--nav-bg)]/80 text-sm text-slate-800 dark:text-[color:var(--app-text)] shadow-[0_8px_16px_rgba(15,23,42,0.08)] hover:bg-amber-50 dark:hover:bg-amber-500/10 transition-colors cursor-pointer"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">三维目标</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">生成知识与技能、过程与方法、情感态度与价值观目标。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">重难点与准备</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">明确教学重难点及教学准备，便于课堂实施。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15M4.5 12h10.5M4.5 17.25h7" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">教学过程</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">环节清晰、步骤完整，含导入、新授、练习与小结。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-violet-500/15 text-violet-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" /></svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">作业设计</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">配套作业与拓展设计，支持导出 PDF 留存。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <div class="relative z-10 bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-3xl p-4 mb-8 shadow-[0_18px_40px_rgba(15,23,42,0.18)]">
                  <div class="flex flex-col gap-3">
                    <div class="flex flex-wrap items-center justify-end gap-2">
                      <div class="relative">
                        <button
                          type="button"
                          class="h-10 rounded-2xl bg-[color:var(--nav-bg)] border-2 border-[color:var(--nav-active-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors px-4 text-xs font-semibold text-[color:var(--app-text)] inline-flex items-center gap-2 cursor-pointer"
                          :aria-label="'备课资料'"
                          :title="includeMaterials ? '备课资料：是' : '备课资料：否'"
                          @click="includeMaterials = !includeMaterials"
                        >
                          <svg viewBox="0 0 24 24" class="size-5 text-amber-300" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
                          </svg>
                          <span>备课资料：{{ includeMaterials ? "是" : "否" }}</span>
                        </button>
                      </div>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-3 items-stretch">
                      <input
                        v-model="topic"
                        placeholder="输入课题生成教案（例如：一次函数与方程）"
                        class="flex-1 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-3xl px-5 py-3 text-[color:var(--app-text)] placeholder-stone-500 outline-none"
                        @keydown.enter="generate"
                      />
                      <button
                        type="button"
                        :disabled="!topic.trim() || loading"
                        class="rounded-full bg-[color:var(--nav-hover-bg)] hover:bg-[color:var(--nav-hover-bg-strong)] duration-300 transition-all text-[color:var(--app-text)] px-5 py-3 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                        @click="generate"
                      >
                        <template v-if="loading">
                          <svg class="size-4 animate-spin" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" class="opacity-25" />
                            <path d="M4 12a8 8 0 0 1 8-8" class="opacity-75" fill="currentColor" />
                          </svg>
                          正在生成…
                        </template>
                        <template v-else>
                          生成教案
                          <svg viewBox="0 0 24 24" class="size-4" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 12l18-9-6.75 9L21 21 3 12z" fill="currentColor" />
                          </svg>
                        </template>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="mt-10 space-y-4">
            <GenerationStatusCard
              emoji="📝"
              tone="amber"
              title="教案正在生成"
              description="系统正在整理目标、重难点、教学过程与作业设计，请稍候。"
              phase="generating"
              :steps="lessonPlanGenerationSteps"
            />

            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">当前课题</div>
                  <div class="mt-1 text-lg font-semibold text-[color:var(--app-text)]">{{ activeLessonPlanTopic }}</div>
                  <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span class="rounded-full border border-amber-300/60 bg-amber-100/80 px-2.5 py-1 font-semibold text-amber-800">
                      正在生成
                    </span>
                    <span class="rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 px-2.5 py-1 text-[color:var(--nav-text-muted)]">
                      {{ includeMaterials ? "已关联备课资料" : "未关联备课资料" }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="error && !loading" class="mt-4 p-4 rounded-2xl border border-rose-400/50 bg-rose-500/10 text-rose-200 text-sm">
            {{ error }}
          </div>

          <!-- 已生成教案展示 -->
          <div v-else-if="plan" class="space-y-6">
            <div class="flex items-center justify-between flex-wrap gap-3">
              <h2 class="text-lg font-semibold text-[color:var(--app-text)]">{{ plan.title || "教案" }}</h2>
              <div class="flex items-center gap-2">
                <a
                  :href="pdfDownloadUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors inline-flex items-center gap-2 cursor-pointer"
                >
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 10.5v6m0 0l-3-3m3 3l3-3m2 8.25H4.5a2.25 2.25 0 0 1-2.25-2.25V6.75a2.25 2.25 0 0 1 2.25-2.25h15A2.25 2.25 0 0 1 21.75 6.75v11.25a2.25 2.25 0 0 1-2.25 2.25h-5.25" />
                  </svg>
                  导出 PDF
                </a>
                <button
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors cursor-pointer"
                  @click="resetAndNew"
                >
                  再生成一份
                </button>
              </div>
            </div>

            <div class="space-y-6">
              <!-- 一、教学目标（三维目标） -->
              <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <h3 class="text-sm font-bold text-[color:var(--nav-text-muted)] mb-3">一、教学目标（三维目标）</h3>
                <div class="space-y-2 text-sm text-[color:var(--app-text)]">
                  <p v-if="plan.teaching_goals?.knowledge"><span class="font-medium text-amber-600/90">知识与技能：</span>{{ plan.teaching_goals.knowledge }}</p>
                  <p v-if="plan.teaching_goals?.process"><span class="font-medium text-amber-600/90">过程与方法：</span>{{ plan.teaching_goals.process }}</p>
                  <p v-if="plan.teaching_goals?.emotion"><span class="font-medium text-amber-600/90">情感态度与价值观：</span>{{ plan.teaching_goals.emotion }}</p>
                </div>
              </section>

              <!-- 二、教学重难点 -->
              <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <h3 class="text-sm font-bold text-[color:var(--nav-text-muted)] mb-3">二、教学重难点</h3>
                <div class="space-y-2 text-sm text-[color:var(--app-text)]">
                  <p v-if="plan.key_points?.length"><span class="font-medium text-amber-600/90">教学重点：</span>{{ plan.key_points.join("；") }}</p>
                  <p v-if="plan.difficult_points?.length"><span class="font-medium text-amber-600/90">教学难点：</span>{{ plan.difficult_points.join("；") }}</p>
                </div>
              </section>

              <!-- 三、教学准备 -->
              <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <h3 class="text-sm font-bold text-[color:var(--nav-text-muted)] mb-3">三、教学准备</h3>
                <p class="text-sm text-[color:var(--app-text)]">{{ (plan.preparation || []).join("；") || "—" }}</p>
              </section>

              <!-- 四、教学过程 -->
              <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <h3 class="text-sm font-bold text-[color:var(--nav-text-muted)] mb-3">四、教学过程</h3>
                <div class="space-y-4">
                  <div
                    v-for="(step, i) in (plan.process || [])"
                    :key="i"
                    class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-4"
                  >
                    <div class="text-xs font-semibold text-amber-600/90 mb-2">{{ step.title }}</div>
                    <div class="text-sm text-[color:var(--app-text)] whitespace-pre-wrap">{{ step.content }}</div>
                  </div>
                </div>
              </section>

              <!-- 五、作业设计 -->
              <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <h3 class="text-sm font-bold text-[color:var(--nav-text-muted)] mb-3">五、作业设计</h3>
                <p class="text-sm text-[color:var(--app-text)] whitespace-pre-wrap">{{ plan.homework || "—" }}</p>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createLessonPlan,
  getLessonPlanDetail,
  lessonPlanPdfUrl,
  type LessonPlanData,
  type LessonPlanMeta,
} from "../lib/api";
import { getUserScopedStorageKey } from "../lib/userStorage";
import { getRouteState } from "../lib/routerState";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import LessonPlanHistoryPanel from "../components/LessonPlan/LessonPlanHistoryPanel.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

provide("learningFolderKey", computed(() => getUserScopedStorageKey("pagelm-learning-folder-teacher")));
provide("chatRole", computed(() => "teacher" as const));

const route = useRoute();
const router = useRouter();
const historyRef = ref<InstanceType<typeof LessonPlanHistoryPanel> | null>(null);

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("pagelm-learning-folder-teacher"));

const topic = ref("");
const loading = ref(false);
const error = ref("");
const plan = ref<LessonPlanData | null>(null);
const meta = ref<LessonPlanMeta | null>(null);
const lessonPlanId = ref("");
const includeMaterials = ref(false);

const quickTopics = ["一次函数与方程", "牛顿运动定律", "光合作用"];
const lessonPlanGenerationSteps = [{ key: "generating", label: "正在生成教案" }];
const activeLessonPlanTopic = computed(() => topic.value.trim() || "未命名课题");

function onQuickTopic(value: string) {
  if (loading.value) return;
  topic.value = value;
  generate();
}

const pdfDownloadUrl = computed(() =>
  lessonPlanId.value ? lessonPlanPdfUrl(lessonPlanId.value) : ""
);

function loadLearningFolderIds(): string[] {
  try {
    const raw = localStorage.getItem(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
}

async function generate() {
  const t = topic.value.trim();
  if (!t || loading.value) return;

  loading.value = true;
  error.value = "";
  plan.value = null;
  meta.value = null;
  lessonPlanId.value = "";

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const res = await createLessonPlan({
      topic: t,
      includeMaterials: includeMaterials.value && materialIds.length > 0,
      materialIds: includeMaterials.value ? materialIds : [],
    });
    if (res?.ok && res.plan) {
      plan.value = res.plan;
      meta.value = res.meta || null;
      lessonPlanId.value = res.lessonPlanId || "";
      historyRef.value?.loadPlans?.();
    } else {
      error.value = (res as { error?: string })?.error || "生成失败，请重试。";
    }
  } catch (e: unknown) {
    plan.value = null;
    meta.value = null;
    lessonPlanId.value = "";
    const msg = e instanceof Error ? e.message : String(e);
    try {
      const parsed = JSON.parse(msg.replace(/^http \d+: /, "")) as { error?: string };
      error.value = parsed?.error || msg;
    } catch {
      error.value = msg;
    }
  } finally {
    loading.value = false;
  }
}

function resetAndNew() {
  error.value = "";
  plan.value = null;
  meta.value = null;
  lessonPlanId.value = "";
  topic.value = "";
}

async function loadPlan(id: string) {
  if (!id) return;
  try {
    const res = await getLessonPlanDetail(id);
    if (res?.ok && res.plan) {
      plan.value = res.plan;
      meta.value = res.meta || null;
      lessonPlanId.value = id;
      if (res.meta?.title) topic.value = res.meta.title;
    }
  } catch {
    plan.value = null;
    meta.value = null;
    lessonPlanId.value = "";
  }
}

onMounted(() => {
  const id = (route.query.lessonPlanId as string) || getRouteState<{ lessonPlanId?: string }>().lessonPlanId;
  const isNew = route.query.new;
  if (isNew) {
    resetAndNew();
    router.replace({ path: "/lesson-plan" });
  } else if (id) {
    loadPlan(id);
  }
});

watch(
  () => route.query.lessonPlanId,
  (id) => {
    if (id) loadPlan(id as string);
  }
);

watch(
  () => route.query.new,
  (isNew) => {
    if (route.path === "/lesson-plan" && isNew) {
      resetAndNew();
      router.replace({ path: "/lesson-plan" });
    }
  }
);
</script>
