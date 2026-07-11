<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <SlidesHistoryPanel ref="historyPanelRef" class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-semibold text-[color:var(--app-text)] flex items-center gap-3">教学幻灯片</h1>
            </div>
          </div>

          <!-- 空状态：未生成时展示 -->
          <div
            v-if="!generatedSlideId && !connecting"
            class="min-h-[62vh] flex flex-col items-center justify-center"
          >
            <div class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-violet-500/20 to-fuchsia-400/30 border border-violet-400/30 shadow-[0_18px_40px_rgba(139,92,246,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-violet-500" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 19.5h8M10 16.5v3M14 16.5v3" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">生成大纲与配图</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  输入主题即可生成课程大纲与对应配图，页面会直接展示每一页的讲解要点和插图，方便快速备课。
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
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">备课资料可选</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可基于资料夹内容生成更贴合的课件。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8 19.5h8" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">页数灵活</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">10 / 15 / 20 页可选，默认 10 页。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 6.75l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">自动整理结构</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">自动生成课程大纲与每页重点。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-rose-500/15 text-rose-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">课堂配图</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">自动补充适合课堂展示的插图。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <SlidesTopicBar
                  :key="topicBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="handleStart"
                  :isLoading="connecting"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectPageCount="setPageCount"
                  :pageCountValue="pageCount"
                  :pageCountOptions="[5, 10]"
                  materialsLabel="备课资料"
                />
              </div>
            </div>
          </div>

          <!-- 生成中 -->
          <div v-if="connecting" class="mt-10">
            <GenerationStatusCard
              emoji="🖼️"
              tone="violet"
              title="教学幻灯片正在生成"
              description="正在整理每一页的讲解重点和配图，请稍候。"
              phase="generating"
              :steps="slidesGenerationSteps"
            />
          </div>

          <!-- 错误提示 -->
          <div v-if="generateError && !connecting" class="mt-6 rounded-2xl border border-rose-300 bg-rose-50/80 dark:bg-rose-900/20 p-4 text-rose-700 dark:text-rose-300 text-sm">
            {{ friendlyGenerateError }}
            <button type="button" class="mt-2 underline" @click="generateError = ''">关闭</button>
          </div>

          <!-- 生成结果：大纲与配图展示 -->
          <div v-if="generatedSlideId && !connecting && !generateError" class="space-y-6 min-h-[88vh] flex flex-col">
            <div class="flex items-center justify-between flex-wrap gap-3 shrink-0">
              <h2 class="text-lg font-semibold text-[color:var(--app-text)]">大纲与配图</h2>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white text-sm font-semibold shadow-[0_10px_18px_rgba(139,92,246,0.25)] hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed transition-colors cursor-pointer"
                  :disabled="pptDownloading"
                  @click="downloadCurrentPptx"
                >
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 20h14" />
                  </svg>
                  {{ pptDownloading ? "正在准备PPT" : "移植到ppt文件" }}
                </button>
                <button
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors cursor-pointer"
                  @click="showOutlineSummary = true"
                >
                  大纲汇总
                </button>
                <button
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors cursor-pointer"
                  @click="showImageSummary = true"
                >
                  配图汇总
                </button>
                <button
                  type="button"
                  class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors cursor-pointer"
                  @click="newSlides"
                >
                  再生成一份
                </button>
              </div>
            </div>
            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-8 md:p-10 shadow-[0_12px_26px_rgba(15,23,42,0.12)] flex-1 min-h-0 flex flex-col">
              <p class="text-sm text-[color:var(--nav-text-muted)] mb-4 shrink-0">{{ generatedTitle || topic }} · 共 {{ generatedSlides.length }} 页</p>
              <p
                v-if="missingImageCount > 0"
                class="text-sm text-amber-600 mb-4 shrink-0"
              >
                目前有 {{ missingImageCount }} 页配图还没有补齐，你可以稍后再试一次。
              </p>
              <p
                v-if="pptDownloadError"
                class="text-sm text-rose-600 mb-4 shrink-0"
              >
                {{ pptDownloadError }}
              </p>
              <div class="space-y-5 min-h-[70vh] max-h-[80vh] overflow-y-auto pr-2 flex-1">
                <div
                  v-for="(slide, idx) in generatedSlides"
                  :key="idx"
                  class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] p-5"
                >
                  <h3 class="text-base font-semibold text-[color:var(--app-text)] mb-2">{{ slide.title }}</h3>
                  <ul v-if="slide.bullets?.length" class="list-disc list-inside text-sm text-[color:var(--app-text)] space-y-1">
                    <li v-for="(b, i) in slide.bullets" :key="i">{{ b }}</li>
                  </ul>
                  <button
                    v-if="slide.imageUrl"
                    type="button"
                    class="mt-3 block w-full text-left rounded-xl overflow-hidden border border-[color:var(--nav-border)] hover:opacity-90 transition-opacity cursor-pointer focus:outline-none focus:ring-2 focus:ring-violet-400"
                    @click="previewImageUrl = slide.imageUrl"
                  >
                    <img
                      :src="slide.imageUrl"
                      :alt="slide.title"
                      class="max-h-56 object-cover w-full"
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 单张图片预览弹窗 -->
          <Teleport to="body">
            <div
              v-if="previewImageUrl"
              class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
              @click.self="previewImageUrl = ''"
            >
              <button
                type="button"
                class="absolute top-4 right-4 z-10 rounded-full bg-white/90 p-2 text-slate-700 hover:bg-white transition-colors cursor-pointer"
                aria-label="关闭"
                @click="previewImageUrl = ''"
              >
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
              </button>
              <img
                :src="previewImageUrl"
                alt="预览"
                class="max-w-full max-h-[90vh] object-contain rounded-xl shadow-2xl"
                @click.stop
              />
            </div>
          </Teleport>

          <!-- 大纲汇总弹窗 -->
          <Teleport to="body">
            <div
              v-if="showOutlineSummary"
              class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
              @click.self="showOutlineSummary = false"
            >
              <div class="bg-[color:var(--app-bg)] rounded-3xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col border border-[color:var(--glass-border)]">
                <div class="flex items-center justify-between p-4 border-b border-[color:var(--nav-border)]">
                  <h3 class="text-lg font-semibold text-[color:var(--app-text)]">大纲汇总</h3>
                  <button type="button" class="rounded-xl p-2 text-[color:var(--nav-text-muted)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer" @click="showOutlineSummary = false" aria-label="关闭">
                    <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <div class="flex-1 overflow-y-auto p-4 space-y-4">
                  <div v-for="(slide, idx) in generatedSlides" :key="idx" class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] p-4">
                    <h4 class="text-sm font-semibold text-[color:var(--app-text)] mb-2">{{ idx + 1 }}. {{ slide.title }}</h4>
                    <ul v-if="slide.bullets?.length" class="list-disc list-inside text-sm text-[color:var(--app-text)] space-y-0.5">
                      <li v-for="(b, i) in slide.bullets" :key="i">{{ b }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </Teleport>

          <!-- 配图汇总弹窗（小图网格，点击可放大） -->
          <Teleport to="body">
            <div
              v-if="showImageSummary"
              class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
              @click.self="showImageSummary = false"
            >
              <div class="bg-[color:var(--app-bg)] rounded-3xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col border border-[color:var(--glass-border)]">
                <div class="flex items-center justify-between p-4 border-b border-[color:var(--nav-border)]">
                  <h3 class="text-lg font-semibold text-[color:var(--app-text)]">配图汇总</h3>
                  <button type="button" class="rounded-xl p-2 text-[color:var(--nav-text-muted)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer" @click="showImageSummary = false" aria-label="关闭">
                    <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <div class="flex-1 overflow-y-auto p-4">
                  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    <button
                      v-for="(slide, idx) in generatedSlides"
                      :key="idx"
                      v-show="slide.imageUrl"
                      type="button"
                      class="rounded-xl overflow-hidden border border-[color:var(--nav-border)] hover:ring-2 hover:ring-violet-400 transition-all cursor-pointer focus:outline-none text-left"
                      @click="showImageSummary = false; previewImageUrl = slide.imageUrl!"
                    >
                      <img :src="slide.imageUrl!" :alt="slide.title" class="w-full aspect-square object-cover" />
                      <div class="p-2 text-xs text-[color:var(--nav-text-muted)] truncate">{{ slide.title }}</div>
                    </button>
                  </div>
                  <p v-if="!generatedSlides.some(s => s.imageUrl)" class="text-sm text-[color:var(--nav-text-muted)]">暂无配图</p>
                </div>
              </div>
            </div>
          </Teleport>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import SlidesHistoryPanel, { type SlideRecord } from "../components/Slides/SlidesHistoryPanel.vue";
import SlidesTopicBar from "../components/Slides/SlidesTopicBar.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";
import { env } from "../config/env";
import { downloadSlidePptx, friendlyTaskMessage, generateSlides, getSlideDetail, err as apiErr, type SlideItem } from "../lib/api";
import { getUserScopedStorageKey, readScopedStorage } from "../lib/userStorage";

const learningFolderKey = computed(() => getUserScopedStorageKey("edumind-learning-folder-teacher"));
provide("learningFolderKey", learningFolderKey);
provide("chatRole", computed(() => "teacher" as const));

const route = useRoute();
const topic = ref((route.query.topic as string) || "");
const includeMaterials = ref(false);
const pageCount = ref(10);
const connecting = ref(false);
const generatedSlideId = ref("");
const generatedTitle = ref("");
const generatedSlides = ref<SlideItem[]>([]);
const downloadUrl = ref("");
const pptDownloading = ref(false);
const pptDownloadError = ref("");
const generateError = ref("");
const topicBarKey = ref(0);
const historyPanelRef = ref<InstanceType<typeof SlidesHistoryPanel> | null>(null);
const previewImageUrl = ref("");
const showOutlineSummary = ref(false);
const showImageSummary = ref(false);
const slidesGenerationSteps = [
  { key: "generating", label: "正在生成大纲与配图" },
  { key: "done", label: "正在整理展示结果" },
];

const quickTopics = ["牛顿运动定律", "二次函数与图像", "细胞的结构与功能", "世界地理概览"];
const missingImageCount = computed(() => generatedSlides.value.filter((s) => !s.imageUrl).length);
const slidesHistoryKey = computed(() => getUserScopedStorageKey("edumind-slides-history"));
const friendlyGenerateError = computed(() =>
  generateError.value
    ? friendlyTaskMessage(generateError.value, { feature: "slides" })
    : "",
);

const readSlidesHistory = () => {
  try {
    const raw = readScopedStorage("edumind-slides-history");
    const parsed = raw ? (JSON.parse(raw) as SlideRecord[]) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [] as SlideRecord[];
  }
};

const writeSlidesHistory = (records: SlideRecord[]) => {
  localStorage.setItem(slidesHistoryKey.value, JSON.stringify(records));
  historyPanelRef.value?.loadSlides?.();
};

const loadLearningFolderIds = () => {
  try {
    const raw = readScopedStorage(learningFolderKey.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
};

const addPendingSlideRecord = (title: string) => {
  const tempId = `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const next = readSlidesHistory().filter((item) => item.id !== tempId);
  next.unshift({
    id: tempId,
    title,
    pageCount: pageCount.value,
    at: Date.now(),
    status: "generating",
  });
  writeSlidesHistory(next);
  return tempId;
};

const finalizeSlideRecord = (tempId: string, slideId: string, title: string, totalPages: number) => {
  const next = readSlidesHistory().filter((item) => item.id !== tempId && item.id !== slideId);
  next.unshift({
    id: slideId,
    title,
    pageCount: totalPages,
    at: Date.now(),
    status: "ready",
  });
  writeSlidesHistory(next);
};

const removeSlideRecord = (tempId: string) => {
  const next = readSlidesHistory().filter((item) => item.id !== tempId);
  writeSlidesHistory(next);
};

const setTopic = (v: string) => {
  topic.value = v;
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const setPageCount = (next: number) => {
  pageCount.value = next;
};

const onQuickTopic = (value: string) => {
  if (connecting.value) return;
  topic.value = value;
  handleStart();
};

const handleStart = async () => {
  const trimmed = topic.value.trim();
  if (!trimmed || connecting.value) return;

  const pendingRecordId = addPendingSlideRecord(trimmed);
  connecting.value = true;
  generateError.value = "";
  generatedSlideId.value = "";
  generatedTitle.value = "";
  generatedSlides.value = [];
  downloadUrl.value = "";
  pptDownloadError.value = "";

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const res = await generateSlides({
      topic: trimmed,
      pageCount: pageCount.value,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
    });
    if (!res.ok || !res.slideId) {
      generateError.value = res.error || "生成失败";
      removeSlideRecord(pendingRecordId);
      return;
    }
    generatedSlideId.value = res.slideId;
    generatedTitle.value = res.title ?? trimmed;
    generatedSlides.value = res.slides ?? [];
    downloadUrl.value = res.downloadUrl ? `${env.backend}${res.downloadUrl}` : "";
    pptDownloadError.value = "";
    finalizeSlideRecord(pendingRecordId, res.slideId, trimmed, res.pageCount ?? pageCount.value);
  } catch (e) {
    generateError.value = apiErr(e);
    removeSlideRecord(pendingRecordId);
  } finally {
    connecting.value = false;
  }
};

const newSlides = () => {
  generatedSlideId.value = "";
  generatedTitle.value = "";
  generatedSlides.value = [];
  downloadUrl.value = "";
  pptDownloadError.value = "";
  generateError.value = "";
  topic.value = "";
  topicBarKey.value += 1;
};

// 从历史打开某条幻灯片时加载详情
async function loadSlideFromQuery(slideId: string) {
  if (!slideId || connecting.value) return;
  connecting.value = true;
  generateError.value = "";
  try {
    const res = await getSlideDetail(slideId);
    if (res.ok && res.slide && res.slides) {
      generatedSlideId.value = res.slide.id;
      generatedTitle.value = res.slide.title ?? "";
      generatedSlides.value = res.slides;
      downloadUrl.value = res.slide.downloadUrl ? `${env.backend}${res.slide.downloadUrl}` : "";
      pptDownloadError.value = "";
      topic.value = res.slide.title ?? "";
    }
  } catch {
    generateError.value = "加载幻灯片失败";
  } finally {
    connecting.value = false;
  }
}

const savePptxBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1200);
};

const downloadCurrentPptx = async () => {
  if (!generatedSlideId.value || pptDownloading.value) return;
  pptDownloading.value = true;
  pptDownloadError.value = "";
  try {
    const { blob, filename } = await downloadSlidePptx(generatedSlideId.value);
    savePptxBlob(blob, filename);
  } catch (e) {
    pptDownloadError.value = apiErr(e);
  } finally {
    pptDownloading.value = false;
  }
};

watch(
  () => route.query.slideId as string | undefined,
  (id) => {
    if (route.path === "/slides" && id) loadSlideFromQuery(id);
  },
  { immediate: true }
);

watch(
  () => route.query.new,
  () => {
    if (route.path === "/slides") {
      newSlides();
    }
  }
);
</script>
