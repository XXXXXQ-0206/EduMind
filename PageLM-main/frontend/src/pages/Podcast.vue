<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <PodcastHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="mb-6 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <h1 class="flex items-center gap-3 text-2xl font-semibold text-[color:var(--app-text)]">AI 播客</h1>
            </div>
          </div>

          <div
            v-if="viewState === 'composer'"
            class="flex min-h-[62vh] flex-col items-center justify-center"
          >
            <div class="mx-auto w-full max-w-3xl">
              <div class="flex flex-col items-center gap-3 text-center">
                <div class="flex size-16 items-center justify-center rounded-3xl border border-sky-400/30 bg-gradient-to-br from-sky-500/20 to-cyan-400/30 shadow-[0_18px_40px_rgba(14,165,233,0.25)]">
                  <svg viewBox="0 0 24 24" class="size-8 text-sky-500" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                  </svg>
                </div>
                <h2 class="text-2xl font-semibold text-[color:var(--app-text)] md:text-3xl">把知识变成可听的播客</h2>
                <p class="max-w-2xl text-sm text-[color:var(--nav-text-muted)] md:text-base">
                  输入主题即可生成双人对谈播客，支持学习资料引用与音频长度控制。
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="cursor-pointer rounded-full border border-sky-400/30 bg-white/80 px-4 py-2 text-sm text-slate-800 shadow-[0_8px_16px_rgba(15,23,42,0.08)] transition-colors hover:bg-white"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">一键生成</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">主题输入后快速生成音频。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12a7.5 7.5 0 1 1 15 0 7.5 7.5 0 0 1-15 0Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">资料加持</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可结合上传资料生成内容。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                        <circle cx="12" cy="12" r="9" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">长度可调</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">短/中/长三种时长。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-indigo-500/15 text-indigo-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">历史可追溯</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">随时下载与回听。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <PodcastTopicBar
                  :key="podcastBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="() => start(topic)"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectLength="setLength"
                  :lengthValue="length"
                  :isLoading="false"
                />
              </div>
            </div>
          </div>

          <div v-else-if="viewState === 'waiting'" class="mt-10 space-y-4">
            <GenerationStatusCard
              emoji="🎙️"
              tone="amber"
              :title="waitingTitle"
              :description="waitingDescription"
              :phase="podcastPhase"
              :steps="podcastGenerationSteps"
            />

            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">当前任务</div>
                  <div class="mt-1 text-lg font-semibold text-[color:var(--app-text)]">{{ topic || "未命名播客" }}</div>
                  <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span
                      class="rounded-full border px-2.5 py-1 font-semibold"
                      :class="podcastStatusTone"
                    >
                      {{ podcastStatusLabel }}
                    </span>
                    <span v-if="pid" class="rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 px-2.5 py-1 text-[color:var(--nav-text-muted)]">
                      ID {{ shortPid }}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-4 py-2 text-sm font-medium text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]"
                  @click="createNewPodcast"
                >
                  新建播客
                </button>
              </div>

              <div class="mt-4 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4 text-sm text-[color:var(--nav-text)]">
                {{ friendlyPodcastError || waitingHint }}
              </div>
            </div>
          </div>

          <div v-else class="space-y-6">
            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] p-6 shadow-[0_16px_36px_rgba(0,0,0,0.3)]">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">AI 播客</div>
                  <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ script?.title || topic || "未命名播客" }}</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <a
                    v-if="downloadUrl"
                    :href="downloadUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 rounded-full border border-emerald-300/60 bg-gradient-to-r from-emerald-400 to-lime-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 shadow-[0_12px_24px_rgba(16,185,129,0.35)] transition-all hover:brightness-110"
                  >
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                    </svg>
                    下载音频
                  </a>
                  <button
                    type="button"
                    class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-4 py-2.5 text-sm font-medium text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]"
                    @click="createNewPodcast"
                  >
                    新建播客
                  </button>
                </div>
              </div>
            </div>

            <div
              v-if="podcastError && !audioUrl"
              class="rounded-3xl border border-amber-200/70 bg-amber-50/90 p-5 text-sm text-amber-900 shadow-[0_10px_24px_rgba(217,119,6,0.12)]"
            >
              {{ readyWarningText }}
            </div>

            <div v-if="audioUrl" class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="text-sm font-semibold text-[color:var(--app-text)]">音频播放器</div>
                <div v-if="audioDuration > 0" class="text-xs text-[color:var(--nav-text-muted)]">
                  {{ formatAudioTime(audioCurrentTime) }} / {{ formatAudioTime(audioDuration) }}
                </div>
              </div>

              <div
                v-if="audioDuration > 0"
                ref="progressBarRef"
                class="mt-4 h-2 cursor-pointer overflow-hidden rounded-full bg-[color:var(--nav-bg)]"
                @click="seekAudio($event)"
              >
                <div
                  class="h-full rounded-full bg-gradient-to-r from-sky-400 to-cyan-400 transition-[width] duration-200"
                  :style="{ width: audioProgress + '%' }"
                />
              </div>

              <div class="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  class="inline-flex size-12 cursor-pointer items-center justify-center rounded-full border border-sky-300/60 bg-gradient-to-r from-sky-400 to-cyan-400 text-slate-950 shadow-[0_10px_20px_rgba(56,189,248,0.35)] transition-all hover:brightness-110 disabled:opacity-50"
                  :disabled="!audioUrl"
                  @click="togglePlayPause"
                >
                  <svg v-if="!isPlaying" viewBox="0 0 24 24" class="ml-0.5 size-6" fill="currentColor" aria-hidden="true">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" class="size-6" fill="currentColor" aria-hidden="true">
                    <path d="M7 5h4v14H7zM13 5h4v14h-4z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="inline-flex size-10 cursor-pointer items-center justify-center rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)] disabled:opacity-50"
                  :disabled="!audioUrl"
                  title="后退 10 秒"
                  @click="rewindAudio"
                >
                  <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 9l-3 3m0 0l3 3m-3-3h7.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="inline-flex size-10 cursor-pointer items-center justify-center rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)] disabled:opacity-50"
                  :disabled="!audioUrl"
                  title="快进 10 秒"
                  @click="forwardAudio"
                >
                  <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12.75 15l3-3m0 0l-3-3m3 3h-7.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <span class="ml-2 text-sm font-medium text-[color:var(--app-text)]">
                  {{ isPlaying ? "正在播放" : "已暂停" }}
                </span>
              </div>

              <audio
                ref="audioRef"
                class="hidden"
                preload="auto"
                :src="audioUrl || undefined"
                @play="isPlaying = true"
                @pause="isPlaying = false"
                @ended="isPlaying = false; audioCurrentTime = 0"
                @timeupdate="onTimeUpdate"
                @loadedmetadata="onLoadedMetadata"
                @error="onAudioError"
              >
                您的浏览器不支持音频播放。
              </audio>
              <div v-if="audioError" class="mt-3 text-xs text-rose-400">
                音频加载失败，请尝试下载后播放。
              </div>
            </div>

            <div class="grid gap-4">
              <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <div class="text-sm font-semibold text-[color:var(--app-text)]">播客摘要</div>
                <div class="mt-3 whitespace-pre-wrap text-sm text-[color:var(--nav-text)]">
                  {{ script?.summary || "" }}
                </div>
              </div>
              <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <div class="text-sm font-semibold text-[color:var(--app-text)]">播客脚本</div>
                <div v-if="script?.segments?.length" class="mt-4 space-y-4">
                  <div v-for="(seg, i) in script.segments" :key="i" class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                    <div class="text-xs text-[color:var(--nav-text-muted)]">{{ seg.spk === "A" ? "主持人 A" : "主持人 B" }}</div>
                    <div class="mt-2 text-sm leading-relaxed text-[color:var(--nav-text)]">
                      <MarkdownView :md="seg.md" />
                    </div>
                  </div>
                </div>
                <div v-else class="mt-3 text-sm text-[color:var(--nav-text-muted)]">暂无脚本内容</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  connectPodcastStream,
  friendlyTaskMessage,
  getPodcastDetail,
  podcastStart,
  type GenerationRecordStatus,
  type PodcastEvent,
  type PodcastMeta,
  type PodcastScript,
} from "../lib/api";
import { env } from "../config/env";
import { getUserScopedStorageKey } from "../lib/userStorage";
import { getRouteState } from "../lib/routerState";
import { getAuthToken } from "../lib/auth";
import MarkdownView from "../components/Chat/MarkdownView.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import PodcastHistoryPanel from "../components/Podcast/PodcastHistoryPanel.vue";
import PodcastTopicBar from "../components/Podcast/PodcastTopicBar.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

type PodcastViewState = "composer" | "waiting" | "ready";

const route = useRoute();
const router = useRouter();

const passedPid = getRouteState<{ pid?: string }>().pid || "";
const initialPid = (route.query.pid as string) || passedPid || "";

const topic = ref("");
const pid = ref(initialPid);
const viewState = ref<PodcastViewState>(initialPid ? "waiting" : "composer");
const podcastPhase = ref("generating");
const podcastStatus = ref<GenerationRecordStatus>("pending");
const podcastError = ref("");
const includeMaterials = ref(false);
const length = ref<"short" | "medium" | "long">("medium");
const audioUrl = ref<string | null>(null);
const downloadUrl = ref<string | null>(null);
const script = ref<PodcastScript | null>(null);
const audioRef = ref<HTMLAudioElement | null>(null);
const progressBarRef = ref<HTMLDivElement | null>(null);
const isPlaying = ref(false);
const audioCurrentTime = ref(0);
const audioDuration = ref(0);
const audioError = ref(false);
const podcastBarKey = ref(0);
const quickTopics = ["计算机网络", "世界历史概览", "心理学入门", "生物进化", "人工智能伦理"];
const podcastGenerationSteps = [
  { key: "generating", label: "正在整理脚本" },
  { key: "script", label: "脚本已经准备好" },
  { key: "audio", label: "正在准备音频" },
];

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("pagelm-learning-folder"));
const closeRef = ref<null | (() => void)>(null);
const activeStreamPid = ref<string | null>(null);
const activeRunId = ref(0);
let detailPollTimer: number | null = null;

const shortPid = computed(() => (pid.value ? pid.value.slice(0, 8) : ""));
const audioProgress = computed(() => {
  if (!audioDuration.value) return 0;
  return (audioCurrentTime.value / audioDuration.value) * 100;
});
const podcastStatusLabel = computed(() => {
  if (podcastStatus.value === "ready") return "已完成";
  if (podcastStatus.value === "error") return "生成失败";
  if (podcastStatus.value === "generating") return "合成中";
  return "生成中";
});
const friendlyPodcastError = computed(() =>
  podcastError.value
    ? friendlyTaskMessage(podcastError.value, { feature: "podcast" })
    : "",
);
const podcastStatusTone = computed(() => {
  if (podcastStatus.value === "ready") return "border-emerald-300/60 bg-emerald-100/80 text-emerald-800";
  if (podcastStatus.value === "error") return "border-rose-300/60 bg-rose-100/80 text-rose-700";
  if (podcastStatus.value === "generating") return "border-sky-300/60 bg-sky-100/80 text-sky-700";
  return "border-amber-300/60 bg-amber-100/80 text-amber-800";
});
const waitingTitle = computed(() => {
  if (podcastStatus.value === "error") return "AI 播客未生成成功";
  if (podcastPhase.value === "audio" || podcastStatus.value === "generating") return "脚本已完成，正在合成音频";
  if (podcastPhase.value === "script") return "脚本已经整理好";
  return "AI 播客正在生成脚本";
});
const waitingDescription = computed(() => {
  if (podcastStatus.value === "error") return "这次没有顺利完成，你可以直接重新开始。";
  return "提交后页面会继续等待，脚本和音频准备好后会自动显示出来。";
});
const waitingHint = computed(() => {
  if (podcastStatus.value === "error") return "旧任务已停止等待。点击“新建播客”即可重新开始。";
  if (podcastStatus.value === "generating" || podcastPhase.value === "audio") {
    return "脚本已经准备好，正在继续生成音频；如果这次只拿到脚本，也会先展示给你。";
  }
  if (script.value?.segments?.length) {
    return "脚本内容已经可以阅读了，音频一准备好就会自动补上。";
  }
  return "内容生成中，请稍等，准备好后会自动展示。";
});
const readyWarningText = computed(() => {
  if (!podcastError.value) return "";
  return `${friendlyPodcastError.value} 你可以先阅读脚本，稍后再决定是否重新生成音频。`;
});

const nextRunId = () => {
  activeRunId.value += 1;
  return activeRunId.value;
};

const isActiveRun = (runId: number) => activeRunId.value === runId;

const notifyHistoryUpdated = (nextPid?: string) => {
  try {
    window.dispatchEvent(new CustomEvent("podcast:updated", { detail: { pid: nextPid || pid.value } }));
  } catch {
    return;
  }
};

const clearDetailPolling = () => {
  if (detailPollTimer !== null) {
    window.clearTimeout(detailPollTimer);
    detailPollTimer = null;
  }
};

const clearStream = () => {
  if (!closeRef.value) return;
  closeRef.value();
  closeRef.value = null;
  activeStreamPid.value = null;
};

const resetAudioState = () => {
  if (audioRef.value) {
    audioRef.value.pause();
    audioRef.value.currentTime = 0;
  }
  isPlaying.value = false;
  audioCurrentTime.value = 0;
  audioDuration.value = 0;
  audioError.value = false;
};

const resetState = () => {
  nextRunId();
  clearDetailPolling();
  clearStream();
  resetAudioState();
  viewState.value = "composer";
  topic.value = "";
  pid.value = "";
  includeMaterials.value = false;
  length.value = "medium";
  podcastPhase.value = "generating";
  podcastStatus.value = "pending";
  podcastError.value = "";
  audioUrl.value = null;
  downloadUrl.value = null;
  script.value = null;
  podcastBarKey.value += 1;
};

const setTopic = (value: string) => {
  topic.value = value;
};

const onQuickTopic = (value: string) => {
  topic.value = value;
  void start(value);
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const setLength = (next: "short" | "medium" | "long") => {
  length.value = next;
};

const createNewPodcast = () => {
  router.push({ path: "/podcast", query: { new: String(Date.now()) } });
};

const loadLearningFolderIds = () => {
  try {
    const raw = localStorage.getItem(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [] as string[];
  }
};

const formatAudioTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
};

const togglePlayPause = async () => {
  if (!audioRef.value) return;
  try {
    if (isPlaying.value) {
      audioRef.value.pause();
    } else {
      audioError.value = false;
      await audioRef.value.play();
    }
  } catch {
    audioError.value = true;
  }
};

const rewindAudio = () => {
  if (!audioRef.value) return;
  audioRef.value.currentTime = Math.max(0, audioRef.value.currentTime - 10);
};

const forwardAudio = () => {
  if (!audioRef.value) return;
  audioRef.value.currentTime = Math.min(audioRef.value.duration || 0, audioRef.value.currentTime + 10);
};

const seekAudio = (e: MouseEvent) => {
  if (!audioRef.value || !progressBarRef.value || !audioDuration.value) return;
  const rect = progressBarRef.value.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  audioRef.value.currentTime = ratio * audioDuration.value;
};

const onTimeUpdate = () => {
  if (!audioRef.value) return;
  audioCurrentTime.value = audioRef.value.currentTime;
};

const onLoadedMetadata = () => {
  if (!audioRef.value) return;
  audioDuration.value = audioRef.value.duration || 0;
  audioError.value = false;
};

const onAudioError = () => {
  audioError.value = true;
  isPlaying.value = false;
};

const resolveBackendMediaUrl = (raw?: string | null) => {
  if (!raw) return null;
  const value = String(raw).trim();
  if (!value) return null;
  try {
    const backend = new URL(env.backend);
    const parsed = new URL(value, env.backend);
    const isPodcastAsset =
      parsed.pathname.includes("/storage/podcasts/") ||
      parsed.pathname.includes("/podcast/download/");

    if (isPodcastAsset && parsed.origin !== backend.origin && parsed.hostname === backend.hostname) {
      return `${backend.origin}${parsed.pathname}${parsed.search}${parsed.hash}`;
    }
    return parsed.toString();
  } catch {
    return value;
  }
};

const withDownloadToken = (raw?: string | null) => {
  const resolved = resolveBackendMediaUrl(raw);
  if (!resolved) return null;
  try {
    const token = getAuthToken();
    if (!token) return resolved;
    const parsed = new URL(resolved, env.backend);
    if (!parsed.pathname.includes("/podcast/download/")) return parsed.toString();
    parsed.searchParams.set("token", token);
    return parsed.toString();
  } catch {
    return resolved;
  }
};

const applyPodcastDetail = (id: string, meta: PodcastMeta, nextScript: PodcastScript | null) => {
  pid.value = meta.id || id;
  topic.value = meta.title || topic.value;
  length.value = (meta.length as "short" | "medium" | "long") || length.value;
  downloadUrl.value = withDownloadToken(meta.file || null);
  audioUrl.value = resolveBackendMediaUrl(meta.static || meta.file || null);
  script.value = nextScript || null;
  podcastStatus.value = meta.status || (meta.file || meta.static ? "ready" : "pending");
  podcastError.value = meta.error || "";

  if (script.value?.segments?.length) {
    podcastPhase.value = podcastStatus.value === "ready" ? "audio" : "script";
  }
  if (podcastStatus.value === "generating") {
    podcastPhase.value = "audio";
  }

  notifyHistoryUpdated(id);

  const isReady = Boolean(audioUrl.value || (podcastStatus.value === "ready" && script.value));
  if (isReady) {
    viewState.value = "ready";
    clearDetailPolling();
    return true;
  }

  viewState.value = "waiting";
  if (podcastStatus.value === "error") {
    clearDetailPolling();
  }
  return false;
};

const connectStreamForPid = (targetPid: string, runId: number) => {
  if (!targetPid || !isActiveRun(runId)) return;
  if (activeStreamPid.value === targetPid && closeRef.value) return;

  clearStream();

  const { close } = connectPodcastStream(targetPid, (ev: PodcastEvent) => {
    if (!isActiveRun(runId)) return;
    if (ev.type === "phase" && ev.value) {
      podcastPhase.value = ev.value;
    }
    if (ev.type === "script") {
      podcastPhase.value = "script";
      void fetchPodcastDetail(targetPid, runId);
    }
    if (ev.type === "audio") {
      podcastPhase.value = "audio";
      void fetchPodcastDetail(targetPid, runId);
    }
    if (ev.type === "warn" && ev.message) {
      podcastError.value = ev.message;
      scheduleDetailPolling(targetPid, runId, 0);
    }
    if (ev.type === "error") {
      if (ev.error && !podcastError.value) {
        podcastError.value = ev.error;
      }
      scheduleDetailPolling(targetPid, runId, 0);
    }
    if (ev.type === "done") {
      close();
      closeRef.value = null;
      activeStreamPid.value = null;
      scheduleDetailPolling(targetPid, runId, 0);
    }
    if (ev.type === "close") {
      closeRef.value = null;
      activeStreamPid.value = null;
      scheduleDetailPolling(targetPid, runId, 0);
    }
  });

  closeRef.value = () => {
    close();
    closeRef.value = null;
    activeStreamPid.value = null;
  };
  activeStreamPid.value = targetPid;
};

const fetchPodcastDetail = async (id: string, runId: number) => {
  if (!id || !isActiveRun(runId)) return false;
  try {
    const res = await getPodcastDetail(id);
    if (!res?.ok || !isActiveRun(runId)) return false;
    return applyPodcastDetail(id, res.podcast, res.script || null);
  } catch {
    return false;
  }
};

const scheduleDetailPolling = (id: string, runId: number, delay = 2200) => {
  if (!id || !isActiveRun(runId)) return;
  clearDetailPolling();
  detailPollTimer = window.setTimeout(async () => {
    detailPollTimer = null;
    if (!isActiveRun(runId)) return;
    const ready = await fetchPodcastDetail(id, runId);
    if (!isActiveRun(runId) || ready || podcastStatus.value === "error") return;
    scheduleDetailPolling(id, runId);
  }, delay);
};

const openExistingPodcast = async (id: string) => {
  if (!id) return;
  const runId = nextRunId();
  clearDetailPolling();
  clearStream();
  resetAudioState();
  viewState.value = "waiting";
  pid.value = id;
  podcastPhase.value = "generating";
  podcastStatus.value = "pending";
  podcastError.value = "";
  audioUrl.value = null;
  downloadUrl.value = null;
  script.value = null;
  connectStreamForPid(id, runId);
  const ready = await fetchPodcastDetail(id, runId);
  if (!isActiveRun(runId) || ready || String(podcastStatus.value) === "error") {
    if (ready || String(podcastStatus.value) === "error") {
      clearStream();
    }
    return;
  }
  scheduleDetailPolling(id, runId, 0);
};

const start = async (input: string) => {
  const trimmed = input.trim();
  const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
  const useMaterials = includeMaterials.value && materialIds.length > 0;
  if (!trimmed && !useMaterials) return;

  const runId = nextRunId();
  clearDetailPolling();
  clearStream();
  resetAudioState();
  viewState.value = "waiting";
  topic.value = trimmed || "基于学习资料的深度解读";
  podcastPhase.value = "generating";
  podcastStatus.value = "pending";
  podcastError.value = "";
  audioUrl.value = null;
  downloadUrl.value = null;
  script.value = null;

  try {
    const res = await podcastStart({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      length: length.value,
    });
    if (!res?.pid) throw new Error("pid missing");
    if (!isActiveRun(runId)) return;

    pid.value = res.pid;
    notifyHistoryUpdated(res.pid);
    scheduleDetailPolling(res.pid, runId, 1200);

    connectStreamForPid(res.pid, runId);

    router.replace({ path: "/podcast", query: { pid: res.pid }, state: { pid: res.pid } });
  } catch (error) {
    if (!isActiveRun(runId)) return;
    podcastStatus.value = "error";
    podcastError.value = error instanceof Error ? error.message : "播客启动失败";
  }
};

onMounted(() => {
  if (initialPid) {
    void openExistingPodcast(initialPid);
  }
});

watch(
  () => route.query.pid,
  async (next) => {
    const nextPid = (next as string) || getRouteState<{ pid?: string }>().pid || "";
    if (!nextPid) {
      resetState();
      return;
    }
    if (nextPid === pid.value && viewState.value !== "composer") return;
    await openExistingPodcast(nextPid);
  },
);

watch(
  () => route.query.t,
  async (next, prev) => {
    if (!next || next === prev) return;
    const nextPid = (route.query.pid as string) || "";
    if (nextPid && route.path === "/podcast") {
      await openExistingPodcast(nextPid);
    }
  },
);

watch(
  () => route.query.new,
  (next) => {
    if (!next || route.query.pid || route.path !== "/podcast") return;
    resetState();
  },
);

onBeforeUnmount(() => {
  clearDetailPolling();
  clearStream();
  resetAudioState();
});
</script>
