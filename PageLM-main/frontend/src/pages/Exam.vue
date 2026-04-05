<template>
  <div v-if="!activeExam" class="min-h-screen w-full px-4 lg:pl-28 lg:pr-4">
    <div class="max-w-5xl mx-auto pt-10 pb-14">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="p-2 rounded-xl bg-stone-950 border border-zinc-800 hover:bg-stone-900 transition-colors"
            aria-label="返回"
            @click="router.back()"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-stone-300" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
            </svg>
          </button>
          <h1 class="text-2xl font-semibold text-white">Exam Labs</h1>
        </div>
        <div class="px-3 py-1 rounded-full bg-gradient-to-r from-sky-500/20 to-blue-500/20 border border-sky-500/30 text-sky-300 text-xs font-medium">
          测试版
        </div>
      </div>

      <LoadingIndicator v-if="loadingExams" label="正在加载考试..." />

      <div class="grid gap-6">
        <div
          v-for="ex in exams"
          :key="ex.id"
          class="group rounded-2xl bg-stone-950 border border-zinc-800 p-5 cursor-pointer hover:border-sky-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-sky-500/10"
          @click="start(ex.id)"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="text-lg font-semibold text-white">{{ ex.name }}</div>
            <div class="px-3 py-1 rounded-full bg-sky-900/30 text-sky-300 text-xs font-medium">
              {{ ex.sections.length }} 个部分
            </div>
          </div>
          <div class="text-sm text-stone-400">点击开始此考试</div>
        </div>
      </div>

      <div v-if="!loadingExams && !exams.length" class="mt-16 text-center text-stone-400">没有可用的考试。</div>
    </div>
  </div>

  <div v-else class="flex flex-col min-h-screen w-full px-4 lg:pl-28 lg:pr-4">
    <div class="w-full max-w-4xl mx-auto p-4 pt-8 pb-24 my-auto">
      <div v-if="connecting" class="mt-10">
        <LoadingIndicator label="正在构建您的考试..." />
      </div>

      <div v-if="qs.length > 0 && !done && q">
        <QuizHeader :topic="activeExam || '考试'" :idx="idx" :total="total" :score="score" />
        <QuestionCard
          :q="q"
          :selected="selected"
          :showExp="showExp"
          :showHint="showHint"
          :onSelect="onSelect"
          :onHint="() => (showHint = true)"
          :onSubmit="onSubmit"
          :onNext="onNext"
          :isLast="idx === total - 1"
        />
      </div>

      <ResultsPanel
        v-if="done"
        :score="score"
        :total="total"
        :percentage="percentage"
        :visual="resultVisual"
        :answers="answers"
        :onRetake="() => start(activeExam || '')"
        :onReview="() => (reviewOpen = true)"
        :onNewTopic="() => (activeExam = null)"
      />

      <ReviewModal v-if="reviewOpen" :answers="answers" :onClose="() => (reviewOpen = false)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getExams, startExam, connectExamStream, type ExamEvent } from "../lib/api";
import LoadingIndicator from "../components/Chat/LoadingIndicator.vue";
import QuizHeader from "../components/Quiz/QuizHeader.vue";
import QuestionCard from "../components/Quiz/QuestionCard.vue";
import ResultsPanel from "../components/Quiz/ResultsPanel.vue";
import ReviewModal from "../components/Quiz/ReviewModal.vue";
import type { Question, UA } from "./Quiz.vue";

type Visual = { msg: string; cls: string; icon: "trophy" | "spark" | "book" | "bolt" };

const router = useRouter();

const exams = ref<any[]>([]);
const loadingExams = ref(true);
const qs = ref<Question[]>([]);
const idx = ref(0);
const score = ref(0);
const selected = ref<number | null>(null);
const showHint = ref(false);
const showExp = ref(false);
const done = ref(false);
const answers = ref<UA[]>([]);
const reviewOpen = ref(false);
const connecting = ref(false);
const activeExam = ref<string | null>(null);
const closeRef = ref<null | (() => void)>(null);

const total = computed(() => qs.value.length);
const q = computed(() => qs.value[idx.value]);
const percentage = computed(() => (total.value ? Math.round((score.value / total.value) * 100) : 0));

const resultVisual = computed<Visual>(() => {
  if (percentage.value >= 90)
    return { msg: "优秀！", cls: "bg-green-900/20 border border-green-700 text-green-200", icon: "trophy" };
  if (percentage.value >= 70)
    return { msg: "做得好！", cls: "bg-blue-900/20 border border-blue-700 text-blue-200", icon: "spark" };
  if (percentage.value >= 50)
    return { msg: "不错的努力！", cls: "bg-yellow-900/20 border border-yellow-700 text-yellow-200", icon: "book" };
  return { msg: "继续学习！", cls: "bg-red-900/20 border border-red-700 text-red-200", icon: "bolt" };
});

const fetchExams = async () => {
  try {
    const r = await getExams();
    exams.value = r.exams || [];
  } finally {
    loadingExams.value = false;
  }
};

const start = async (id: string) => {
  if (!id) return;
  if (closeRef.value) closeRef.value();
  qs.value = [];
  idx.value = 0;
  score.value = 0;
  done.value = false;
  answers.value = [];
  selected.value = null;
  activeExam.value = id;
  connecting.value = true;

  try {
    const { runId } = await startExam(id);
    const { close } = connectExamStream(runId, (ev: ExamEvent) => {
      if (ev.type === "exam") {
        const arr = Array.isArray(ev.payload) ? ev.payload : [];
        qs.value = arr.map((q: any) => ({ ...q, correct: Math.max(0, q.correct - 1) }));
        idx.value = 0;
        connecting.value = false;
      }
      if (ev.type === "done" || ev.type === "error") {
        connecting.value = false;
      }
    });
    closeRef.value = close;
  } catch {
    connecting.value = false;
  }
};

const onSelect = (i: number) => {
  if (!showExp.value) selected.value = i;
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
  };
  answers.value = [...answers.value, ua];
  showExp.value = true;
  if (correct) score.value += 1;
};

const onNext = () => {
  if (!showExp.value) return;
  if (idx.value === total.value - 1) {
    done.value = true;
    return;
  }
  idx.value += 1;
  selected.value = null;
  showHint.value = false;
  showExp.value = false;
};

onMounted(fetchExams);

onBeforeUnmount(() => {
  if (closeRef.value) closeRef.value();
});
</script>
