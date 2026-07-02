<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-stack custom-scroll space-y-8">
        <header class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div class="text-xs text-[color:var(--nav-text-muted)]">错题本 · 题目复习页</div>
            <h1 class="mt-2 text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">
              {{ mode === "wrong" ? "错题复习" : "已掌握复盘" }}
            </h1>
            <p class="mt-2 text-sm text-[color:var(--nav-text-muted)]">
              {{ mode === "wrong" ? "集中重做错题，是否已掌握由你手动标记。" : "已掌握题目回顾，保持正确率。" }}
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="px-4 py-2 rounded-2xl border border-rose-400/40 bg-rose-500/10 text-black text-sm font-semibold hover:bg-rose-500/20 transition-colors cursor-pointer"
              :class="mode === 'wrong' ? 'ring-1 ring-rose-300/60' : ''"
              @click="setMode('wrong')"
            >
              错题复习 · {{ wrongQuestions.length }} 题
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-2xl border border-emerald-400/40 bg-emerald-500/10 text-black text-sm font-semibold hover:bg-emerald-500/20 transition-colors cursor-pointer"
              :class="mode === 'mastered' ? 'ring-1 ring-emerald-300/60' : ''"
              @click="setMode('mastered')"
            >
              已掌握 · {{ masteredQuestions.length }} 题
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-2xl border border-[color:var(--glass-border)] text-sm text-[color:var(--nav-text)] hover:bg-white/5 transition-colors cursor-pointer"
              @click="goBack"
            >
              返回错题本
            </button>
          </div>
        </header>

        <section class="glass-card rounded-3xl p-6 border border-[color:var(--glass-border)] shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
          <div v-if="loading" class="text-sm text-[color:var(--nav-text-muted)]">正在加载题目…</div>
          <div v-else-if="error" class="text-sm text-rose-200">{{ error }}</div>
          <div v-else-if="!questions.length" class="text-sm text-[color:var(--nav-text-muted)]">暂无题目，请先完成测验。</div>

          <div v-else class="space-y-6">
            <div class="flex flex-wrap items-center gap-2">
              <button
                v-for="(item, idx) in questions"
                :key="item.key"
                type="button"
                class="size-10 rounded-full border border-[color:var(--glass-border)] text-sm font-semibold transition-colors cursor-pointer"
                :class="idx === currentIndex ? 'bg-sky-500/20 text-[color:var(--app-text)] ring-1 ring-sky-300/60' : 'bg-white/5 text-[color:var(--nav-text-muted)] hover:bg-white/10'"
                @click="currentIndex = idx"
              >
                {{ idx + 1 }}
              </button>
            </div>

            <div v-if="currentQuestion" class="space-y-4">
              <div class="flex items-center justify-between text-xs text-[color:var(--nav-text-muted)]">
                <span>题目 {{ currentIndex + 1 }} / {{ questions.length }}</span>
                <span>{{ currentQuestion.subject }}</span>
              </div>

              <QuestionCard
                :q="currentQuestion"
                :selected="selectedAnswer"
                :showExp="showExp"
                :showHint="showHint"
                :onSelect="onSelect"
                :onHint="onHint"
                :onSubmit="onSubmit"
                :onNext="onNext"
                :isLast="currentIndex === questions.length - 1"
              />

              <div class="flex flex-wrap items-center gap-3">
                <button
                  v-if="mode === 'wrong'"
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-emerald-500/15 text-black text-sm font-bold hover:bg-emerald-500/25 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                  :disabled="marking"
                  @click="markAsMastered"
                >
                  {{ marking ? "处理中…" : "标记为已掌握" }}
                </button>
                <div v-if="statusMessage" class="text-sm text-[color:var(--nav-text-muted)]">{{ statusMessage }}</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import QuestionCard from "../components/Quiz/QuestionCard.vue";
import {
  getWrongBookSummary,
  saveQuizAttemptAnswer,
  type QuizAttempt,
  type WrongBookSummary,
} from "../lib/api";

const router = useRouter();
const route = useRoute();

const loading = ref(true);
const error = ref("");
const summary = ref<WrongBookSummary | null>(null);
const currentIndex = ref(0);
const selections = ref<Record<string, number>>({});
const expShown = ref<Record<string, boolean>>({});
const hintShown = ref<Record<string, boolean>>({});
const statusMessage = ref("");
const marking = ref(false);

const mode = computed(() => (route.query.mode === "mastered" ? "mastered" : "wrong"));
const wrongQuestions = computed(() => summary.value?.wrongQuestions || []);
const masteredQuestions = computed(() => summary.value?.masteredQuestions || []);
const questions = computed(() => {
  const list = mode.value === "wrong" ? wrongQuestions.value : masteredQuestions.value;
  return list.map((item) => ({ ...item, key: `${item.quizId}-${item.id}` }));
});

const currentQuestion = computed(() => {
  const item = questions.value[currentIndex.value];
  if (!item) return null;
  return {
    id: item.id,
    question: item.title,
    options: item.options,
    correct: item.correct,
    hint: item.hint || "",
    explanation: item.explanation || "",
    imageHtml: "",
    subject: item.subject,
    quizId: item.quizId,
    key: item.key,
  };
});

const selectedAnswer = computed(() => {
  const key = currentQuestion.value?.key;
  if (!key) return null;
  return selections.value[key] ?? null;
});

const showExp = computed(() => {
  const key = currentQuestion.value?.key;
  if (!key) return false;
  return Boolean(expShown.value[key]);
});

const showHint = computed(() => {
  const key = currentQuestion.value?.key;
  if (!key) return false;
  return Boolean(hintShown.value[key]);
});

const loadSummary = async () => {
  loading.value = true;
  error.value = "";
  try {
    const res = await getWrongBookSummary();
    if (!res || !(res as any).ok) {
      throw new Error((res as any)?.error || "错题数据加载失败");
    }
    summary.value = res;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "错题数据加载失败";
  } finally {
    loading.value = false;
  }
};

const setMode = (next: "wrong" | "mastered") => {
  router.replace({ path: "/wrong-book/practice", query: { mode: next } });
};

const goBack = () => {
  router.push({ path: "/wrong-book" });
};

const onSelect = (i: number) => {
  const key = currentQuestion.value?.key;
  if (!key) return;
  selections.value = { ...selections.value, [key]: i };
};

const onHint = () => {
  const key = currentQuestion.value?.key;
  if (!key) return;
  hintShown.value = { ...hintShown.value, [key]: true };
};

const syncAnswer = async (answer: QuizAttempt) => {
  await saveQuizAttemptAnswer(currentQuestion.value?.quizId || "", answer);
};

const onSubmit = async () => {
  if (!currentQuestion.value) return;
  const qid = currentQuestion.value.id;
  const key = currentQuestion.value.key;
  const selected = selections.value[key];
  if (selected == null) return;

  expShown.value = { ...expShown.value, [key]: true };
  const correct = selected === currentQuestion.value.correct;

  const answer: QuizAttempt = {
    questionId: qid,
    selectedAnswer: selected,
    correct,
    question: currentQuestion.value.question,
    selectedOption: currentQuestion.value.options[selected] || "",
    correctOption: currentQuestion.value.options[currentQuestion.value.correct] || "",
    explanation: currentQuestion.value.explanation,
    at: Date.now(),
  };

  if (mode.value === "wrong") {
    statusMessage.value = correct ? "回答正确，可手动标记为已掌握。" : "回答错误，建议再刷一遍。";
    return;
  }
  try {
    await syncAnswer(answer);
    statusMessage.value = correct ? "回答正确，已更新掌握状态。" : "回答错误，建议再刷一遍。";
    await loadSummary();
  } catch {
    statusMessage.value = "作答已记录，稍后请刷新。";
  }
};

const onNext = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1;
  }
};

const markAsMastered = async () => {
  if (!currentQuestion.value) return;
  marking.value = true;
  const qid = currentQuestion.value.id;
  const correct = currentQuestion.value.correct;
  const answer: QuizAttempt = {
    questionId: qid,
    selectedAnswer: correct,
    correct: true,
    question: currentQuestion.value.question,
    selectedOption: currentQuestion.value.options[correct] || "",
    correctOption: currentQuestion.value.options[correct] || "",
    explanation: currentQuestion.value.explanation,
    at: Date.now(),
  };
  try {
    await syncAnswer(answer);
    statusMessage.value = "已标记为已掌握。";
    await loadSummary();
  } catch {
    statusMessage.value = "标记失败，请稍后重试。";
  } finally {
    marking.value = false;
  }
};

watch(
  () => [mode.value, questions.value.length],
  () => {
    currentIndex.value = 0;
    statusMessage.value = "";
    selections.value = {};
    expShown.value = {};
    hintShown.value = {};
  }
);

onMounted(() => {
  loadSummary();
});
</script>
