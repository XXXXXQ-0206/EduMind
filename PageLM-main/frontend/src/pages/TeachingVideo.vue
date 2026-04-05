<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <VideoHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)] flex items-center gap-3">教学视频</h1>
          </div>

          <!-- 空状态：功能介绍、特点、快捷键、输入区 -->
          <div
            v-if="!script && !connecting"
            class="min-h-[62vh] flex flex-col"
          >
            <div class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-violet-500/20 to-purple-400/30 border border-violet-400/30 shadow-[0_18px_40px_rgba(139,92,246,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-violet-500" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">AI 教学微课一键成片</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  输入主题即可生成讲解脚本、课堂画面和配音内容；支持关联备课资料，完成后可直接预览和回看。
                </p>
              </div>

              <!-- 默认主题快捷键 -->
              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="px-4 py-2 rounded-full border border-violet-400/30 bg-white/80 dark:bg-[color:var(--nav-bg)] text-sm text-slate-800 dark:text-[color:var(--app-text)] shadow-[0_8px_16px_rgba(15,23,42,0.08)] hover:bg-white dark:hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <!-- 功能介绍 / 特点 -->
              <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-violet-500/15 text-violet-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">脚本 + 画面 + 配音</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">自动整理讲解稿、课堂画面和配音，一条龙生成有声微课。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">备课资料联动</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可选关联备课资料，生成内容更贴合教材与课堂。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">有声版本地保存</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">合成后的有声视频保存至本地，随时播放、无需担心链接过期。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6.75m0 0v6.75m0-6.75h6.75M12 6H5.25" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">历史预览与回看</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">左侧历史列表支持一键预览有声视频、进入详情查看脚本。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <VideoTopicBar
                  :key="topicBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="(t) => start(t)"
                  :onSelectInclude="setIncludeMaterials"
                  :isLoading="connecting"
                  materialsLabel="备课资料"
                />
              </div>
            </div>
          </div>

          <!-- 生成中 -->
          <div v-if="connecting" class="mt-10">
            <GenerationStatusCard
              emoji="🎬"
              tone="violet"
              title="教学视频正在生成"
              description="系统会先写讲解脚本，再生成配音和画面，完成后自动展示成片。"
              :phase="videoPhase"
              :steps="videoGenerationSteps"
            />
          </div>

          <!-- 生成完成：视频在上方，讲解脚本在下方且默认折叠 -->
          <div v-if="script" class="space-y-6">
            <div class="flex justify-end">
              <button
                type="button"
                class="px-4 py-2 rounded-2xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] text-sm text-[color:var(--app-text)] transition-colors"
                @click="newVideo"
              >
                再生成一个
              </button>
            </div>
            <TeachingVideoStage
              :title="topic || '未命名微课'"
              :script="script"
              :video-src="videoPlayUrl"
              :audio-src="localAudioUrl"
              :phase="videoPhase"
              :video-source="videoSourceType"
            />
            <div v-if="videoError" class="rounded-3xl border border-rose-400/40 bg-rose-500/10 p-5">
              <div class="flex items-center gap-3 text-rose-200">
                <span class="size-10 rounded-2xl bg-rose-500/20 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                  </svg>
                </span>
                <div>
                  <div class="font-semibold">视频画面暂未生成成功</div>
                  <div class="text-xs mt-0.5 opacity-90">{{ friendlyVideoError }}</div>
                </div>
              </div>
            </div>

            <!-- 2. 讲解脚本（默认折叠，可点击展开/收起） -->
            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 shadow-[0_12px_26px_rgba(15,23,42,0.12)] overflow-hidden">
              <button
                type="button"
                class="w-full flex items-center justify-between gap-3 px-5 py-3 text-left text-sm font-semibold text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg)]/50 transition-colors"
                @click="scriptExpanded = !scriptExpanded"
              >
                <span>讲解脚本</span>
                <span class="shrink-0 flex items-center gap-1 text-xs font-normal text-[color:var(--nav-text-muted)]">
                  {{ scriptExpanded ? "收起" : "展开" }}
                  <svg
                    viewBox="0 0 24 24"
                    class="size-4 transition-transform"
                    :class="{ 'rotate-180': scriptExpanded }"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </button>
              <div v-show="scriptExpanded" class="px-5 pb-5 pt-0">
                <div class="text-sm text-[color:var(--app-text)] whitespace-pre-wrap leading-relaxed">{{ script }}</div>
              </div>
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
import { env } from "../config/env";
import { getAuthToken } from "../lib/auth";
import { getUserScopedStorageKey } from "../lib/userStorage";
import { getRouteState } from "../lib/routerState";
import {
  teachingVideoStart,
  connectTeachingVideoStream,
  friendlyTaskMessage,
  getTeachingVideoDetail,
  type TeachingVideoEvent,
} from "../lib/api";
import VideoTopicBar from "../components/TeachingVideo/VideoTopicBar.vue";
import VideoHistoryPanel from "../components/TeachingVideo/VideoHistoryPanel.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";
import TeachingVideoStage from "../components/TeachingVideo/TeachingVideoStage.vue";

const route = useRoute();
const router = useRouter();

provide("videoRole", computed(() => "teacher"));
provide("videoBasePath", computed(() => "/teaching-video"));
const learningFolderKeyComputed = computed(() => getUserScopedStorageKey("pagelm-learning-folder-teacher"));
provide("learningFolderKey", learningFolderKeyComputed);
provide("chatRole", computed(() => "teacher"));
provide("chatBasePath", computed(() => "/teacher/chat"));

const passedTopic = getRouteState<{ topic?: string }>().topic ?? "";
const passedVideoId = getRouteState<{ videoId?: string }>().videoId ?? "";
const initialTopic = (route.query.topic as string) || passedTopic || "";
const initialVideoId = (route.query.videoId as string) || passedVideoId || "";

const topic = ref(initialTopic);
const script = ref("");
const videoUrl = ref("");
const localVideoUrl = ref("");
const localAudioUrl = ref("");
const videoError = ref("");
const videoId = ref(initialVideoId);
const connecting = ref(false);
const videoPhase = ref("script");
const videoSource = ref<"jimeng_remote" | "jimeng_local_merge" | "fallback_local" | "audio_only" | "script_only">("script_only");
const includeMaterials = ref(false);
const topicBarKey = ref(0);
/** 讲解脚本折叠：默认不展开 */
const scriptExpanded = ref(false);

const quickTopics = [
  "牛顿第一定律",
  "光合作用",
  "二次函数图像",
  "辛亥革命",
];
const videoGenerationSteps = [
  { key: "script", label: "正在生成脚本" },
  { key: "audio", label: "正在合成配音" },
  { key: "video", label: "正在生成画面" },
  { key: "video_pending", label: "正在补充课堂画面" },
];

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("pagelm-learning-folder-teacher"));
const closeRef = ref<null | (() => void)>(null);
const activeRunId = ref(0);
const pollAttempt = ref(0);
const detailSignature = ref("");
let detailPollTimer: number | null = null;
const friendlyVideoError = computed(() =>
  videoError.value
    ? friendlyTaskMessage(videoError.value, { feature: "video" })
    : "",
);

const nextRunId = () => {
  activeRunId.value += 1;
  pollAttempt.value = 0;
  detailSignature.value = "";
  return activeRunId.value;
};

const isActiveRun = (id: number) => id === activeRunId.value;

const clearDetailPolling = () => {
  if (detailPollTimer != null) {
    window.clearTimeout(detailPollTimer);
    detailPollTimer = null;
  }
};

const resolveMediaUrl = (raw?: string | null) => {
  if (!raw) return "";
  const value = String(raw).trim();
  if (!value) return "";
  try {
    return new URL(value, env.backend).toString();
  } catch {
    return value;
  }
};

const applyVideoDetail = (vid: string, res: Awaited<ReturnType<typeof getTeachingVideoDetail>>) => {
  if (!res?.ok) return false;
  const nextSignature = JSON.stringify({
    script: res.script ?? "",
    videoUrl: res.videoUrl ?? "",
    localVideoUrl: res.localVideoUrl ?? "",
    localAudioUrl: res.localAudioUrl ?? "",
    videoSource: res.videoSource ?? "",
    videoError: res.videoError ?? "",
    updatedAt: res.video?.updated_at ?? "",
  });
  const changed = nextSignature !== detailSignature.value;
  detailSignature.value = nextSignature;

  script.value = res.script ?? script.value;
  topic.value = res.video?.title ?? topic.value;
  videoId.value = vid;
  videoUrl.value = res.videoUrl ?? "";
  localVideoUrl.value = resolveMediaUrl(res.localVideoUrl ?? "");
  localAudioUrl.value = resolveMediaUrl(res.localAudioUrl ?? "");
  videoSource.value = res.videoSource ?? (localVideoUrl.value ? "fallback_local" : localAudioUrl.value ? "audio_only" : "script_only");
  videoPhase.value = localVideoUrl.value || videoUrl.value ? "video" : localAudioUrl.value ? "audio" : "script";
  videoError.value = res.videoError ?? "";
  if (changed) {
    notifyHistoryUpdated(vid);
  }
  return Boolean(localVideoUrl.value || videoUrl.value || localAudioUrl.value || videoError.value);
};

const fetchVideoDetail = async (vid: string, runId: number) => {
  if (!vid || !isActiveRun(runId)) return false;
  try {
    const res = await getTeachingVideoDetail(vid);
    if (!isActiveRun(runId)) return false;
    return applyVideoDetail(vid, res);
  } catch {
    return false;
  }
};

const scheduleDetailPolling = (vid: string, runId: number, delay = 2000) => {
  if (!vid || !isActiveRun(runId)) return;
  clearDetailPolling();
  detailPollTimer = window.setTimeout(async () => {
    detailPollTimer = null;
    if (!isActiveRun(runId)) return;
    pollAttempt.value += 1;
    if (pollAttempt.value > 120) {
      connecting.value = false;
      if (!videoError.value) {
        videoError.value = "教学视频生成超时，请稍后从历史记录重试。";
      }
      return;
    }
    const settled = await fetchVideoDetail(vid, runId);
    if (settled) {
      connecting.value = false;
      return;
    }
    scheduleDetailPolling(vid, runId, 2600);
  }, delay);
};

const bindTeachingVideoStream = (vid: string, runId: number) => {
  if (!vid || !isActiveRun(runId)) return;
  if (closeRef.value) {
    try { closeRef.value(); } catch {}
  }
  const { close } = connectTeachingVideoStream(vid, (ev: TeachingVideoEvent) => {
    if (!isActiveRun(runId)) return;
    if (ev.type === "phase" && ev.value) {
      videoPhase.value = ev.value;
    }
    if (ev.type === "script" && ev.script) {
      script.value = ev.script;
    }
    if (ev.type === "video" && ev.videoUrl) {
      videoPhase.value = "video";
      videoUrl.value = ev.videoUrl;
      videoSource.value = localVideoUrl.value ? "jimeng_local_merge" : "jimeng_remote";
      videoError.value = "";
      notifyHistoryUpdated(vid);
    }
    if (ev.type === "local_video" && ev.localPath) {
      videoPhase.value = "video";
      localVideoUrl.value = resolveMediaUrl(`/storage/${ev.localPath}`);
      videoSource.value = videoUrl.value ? "jimeng_local_merge" : "fallback_local";
      notifyHistoryUpdated(vid);
    }
    if (ev.type === "local_audio" && ev.audioPath) {
      videoPhase.value = "audio";
      localAudioUrl.value = resolveMediaUrl(`/storage/${ev.audioPath}`);
      if (!videoUrl.value && !localVideoUrl.value) {
        videoSource.value = "audio_only";
      }
      notifyHistoryUpdated(vid);
    }
    if (ev.type === "video_error" && ev.error) {
      videoError.value = ev.error;
    }
    if (ev.type === "done") {
      connecting.value = false;
      void fetchVideoDetail(vid, runId);
    }
    if (ev.type === "close") {
      scheduleDetailPolling(vid, runId, 800);
    }
    if (ev.type === "error") {
      connecting.value = false;
      scheduleDetailPolling(vid, runId, 800);
    }
  });
  closeRef.value = close;
};

const notifyHistoryUpdated = (nextVideoId?: string) => {
  try {
    window.dispatchEvent(new CustomEvent("teaching-video:updated", { detail: { videoId: nextVideoId || videoId.value } }));
  } catch {
    return;
  }
};

/** 优先使用本地有声版，否则用代理流 */
const videoPlayUrl = computed(() => {
  if (!videoId.value) return "";
  if (localVideoUrl.value) return localVideoUrl.value;
  if (videoUrl.value) {
    const token = getAuthToken();
    if (!token) return `${env.backend}/teaching-videos/${videoId.value}/video`;
    return `${env.backend}/teaching-videos/${videoId.value}/video?token=${encodeURIComponent(token)}`;
  }
  return "";
});

const videoSourceType = computed(() => {
  if (videoSource.value && videoSource.value !== "script_only") return videoSource.value;
  if (localVideoUrl.value && videoUrl.value) return "jimeng_local_merge" as const;
  if (videoUrl.value) return "jimeng_remote" as const;
  if (localVideoUrl.value) return "fallback_local" as const;
  if (localAudioUrl.value) return "audio_only" as const;
  return "script_only" as const;
});

const setTopic = (v: string) => {
  topic.value = v;
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const loadLearningFolderIds = (): string[] => {
  try {
    const raw = localStorage.getItem(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
};

const onQuickTopic = (value: string) => {
  if (connecting.value) return;
  topic.value = value;
  start(value);
};

const start = async (t: string) => {
  const trimmed = t.trim();
  if (!trimmed) return;
  if (closeRef.value) closeRef.value();
  const runId = nextRunId();
  clearDetailPolling();

  script.value = "";
  connecting.value = true;
  videoPhase.value = "script";
  localAudioUrl.value = "";
  videoUrl.value = "";
  localVideoUrl.value = "";
  videoSource.value = "script_only";

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const s = await teachingVideoStart({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      role: "teacher",
    });
    videoId.value = s.videoId;
    videoError.value = "";
    bindTeachingVideoStream(s.videoId, runId);

    if (route.query.topic !== trimmed || route.query.videoId !== s.videoId) {
      router.replace({
        path: "/teaching-video",
        query: { topic: trimmed, videoId: s.videoId },
        state: { topic: trimmed, videoId: s.videoId },
      });
    }
  } catch {
    connecting.value = false;
    clearDetailPolling();
  }
};

const loadVideo = async (vid: string) => {
  if (!vid) return;
  try {
    if (closeRef.value) {
      try { closeRef.value(); } catch {}
    }
    const runId = nextRunId();
    clearDetailPolling();
    const res = await getTeachingVideoDetail(vid);
    if (res?.ok && res.script != null) {
      const settled = applyVideoDetail(vid, res);
      connecting.value = !settled;
      if (connecting.value) {
        bindTeachingVideoStream(vid, runId);
        scheduleDetailPolling(vid, runId, 1200);
      }
    }
  } catch {
    return;
  }
};

const newVideo = () => {
  nextRunId();
  clearDetailPolling();
  script.value = "";
  videoUrl.value = "";
  localVideoUrl.value = "";
  localAudioUrl.value = "";
  videoError.value = "";
  videoSource.value = "script_only";
  topic.value = "";
  videoId.value = "";
  videoPhase.value = "script";
  includeMaterials.value = false;
  topicBarKey.value += 1;
  scriptExpanded.value = false;
};

onMounted(() => {
  if (initialVideoId) loadVideo(initialVideoId);
  else if (initialTopic) start(initialTopic);
});

watch(
  () => route.query.videoId,
  async (next) => {
    const vid = ((next as string) || getRouteState<{ videoId?: string }>().videoId) ?? "";
    if (!vid) {
      if (closeRef.value) closeRef.value();
      newVideo();
      return;
    }
    if (vid === videoId.value) return;
    await loadVideo(vid);
  }
);

watch(
  () => route.query.new,
  () => {
    if (route.path === "/teaching-video") {
      if (closeRef.value) closeRef.value();
      newVideo();
    }
  }
);

onBeforeUnmount(() => {
  clearDetailPolling();
  if (closeRef.value) closeRef.value();
});
</script>
