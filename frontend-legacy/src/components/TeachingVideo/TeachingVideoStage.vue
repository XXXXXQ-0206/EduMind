<template>
  <section class="relative overflow-hidden rounded-[34px] border border-white/55 bg-[linear-gradient(145deg,rgba(9,12,22,0.96),rgba(26,35,54,0.94))] p-5 shadow-[0_30px_80px_rgba(15,23,42,0.28)] md:p-6">
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.2),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.24),transparent_36%)]" aria-hidden="true" />
    <div class="relative">
      <div class="space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="inline-flex items-center rounded-full border border-sky-300/30 bg-sky-300/12 px-3 py-1 text-xs font-semibold text-sky-100">
                {{ modeBadgeText }}
              </span>
              <span class="inline-flex items-center rounded-full border border-white/15 bg-white/6 px-3 py-1 text-xs font-medium text-slate-200">
                {{ stageStatus }}
              </span>
            </div>
            <h2 class="mt-3 text-2xl font-semibold tracking-tight text-white md:text-3xl">{{ title }}</h2>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              {{ heroDescription }}
            </p>
          </div>
          <div class="flex items-center gap-2 rounded-2xl border border-white/12 bg-white/8 px-3 py-2 text-xs text-slate-200">
            <span class="inline-flex size-2 rounded-full bg-emerald-400 teaching-stage-pulse" />
            {{ availabilityText }}
          </div>
        </div>

        <div class="relative overflow-hidden rounded-[28px] border border-white/12 bg-slate-950 shadow-[0_20px_50px_rgba(2,6,23,0.45)]">
          <div class="relative aspect-video">
            <video
              v-if="hasVideo"
              :src="videoSrc"
              controls
              playsinline
              class="absolute inset-0 h-full w-full bg-black object-cover"
            />
            <div v-else class="absolute inset-0 overflow-hidden bg-[linear-gradient(145deg,#0f172a,#172554_58%,#1e293b)]">
              <div class="teaching-stage-orb teaching-stage-orb-a" />
              <div class="teaching-stage-orb teaching-stage-orb-b" />
              <div class="absolute inset-x-0 top-0 flex items-center justify-between px-5 py-4 text-xs text-slate-200">
                <span class="rounded-full border border-white/20 bg-white/10 px-3 py-1">AI 微课演示</span>
                <span class="rounded-full border border-white/20 bg-white/10 px-3 py-1">{{ hasAudio ? "边听边看" : "画面准备中" }}</span>
              </div>
              <div class="absolute inset-x-0 top-1/2 -translate-y-1/2 px-6 text-center">
                <div class="mx-auto max-w-2xl rounded-[28px] border border-white/10 bg-white/8 px-6 py-6 shadow-[0_16px_40px_rgba(15,23,42,0.28)] backdrop-blur-md">
                  <div class="text-xs uppercase tracking-[0.34em] text-sky-200/85">Lesson Focus</div>
                  <div class="mt-3 text-2xl font-semibold leading-tight text-white md:text-4xl">{{ currentCue }}</div>
                  <div class="mt-4 flex flex-wrap items-center justify-center gap-2">
                    <span
                      v-for="point in keyPoints.slice(0, 3)"
                      :key="point"
                      class="rounded-full border border-white/18 bg-white/10 px-3 py-1 text-xs text-slate-100"
                    >
                      {{ point }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent px-5 pb-5 pt-16">
                <div class="rounded-2xl border border-white/12 bg-black/28 px-4 py-3 backdrop-blur-md">
                  <div class="text-[11px] uppercase tracking-[0.26em] text-slate-400">字幕</div>
                  <div class="mt-2 text-sm leading-6 text-white md:text-base">{{ currentCue }}</div>
                </div>
              </div>
            </div>

            <div class="pointer-events-none absolute inset-x-0 top-0 bg-gradient-to-b from-black/55 via-black/10 to-transparent px-5 py-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <div class="text-xs uppercase tracking-[0.3em] text-slate-300">Topic</div>
                  <div class="mt-1 text-base font-medium text-white">{{ title }}</div>
                </div>
                <div class="rounded-full border border-white/15 bg-black/18 px-3 py-1 text-xs text-slate-200">
                  {{ sourceBadgeText }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="hasAudio && !hasVideo"
          class="rounded-[26px] border border-white/12 bg-white/6 px-5 py-4 shadow-[0_16px_36px_rgba(15,23,42,0.18)] backdrop-blur-md"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="text-sm font-semibold text-white">讲解配音控制台</div>
              <div class="mt-1 text-xs text-slate-300">音频已经生成，画面区域会跟随播放节奏展示当前知识点。</div>
            </div>
            <div class="text-xs text-slate-300">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
          </div>

          <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/10" @click="seekAudio">
            <div class="h-full rounded-full bg-gradient-to-r from-sky-400 via-cyan-300 to-violet-400" :style="{ width: `${progress}%` }" />
          </div>

          <div class="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="inline-flex size-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-400 to-cyan-300 text-slate-950 shadow-[0_12px_26px_rgba(56,189,248,0.3)] transition hover:brightness-110"
              @click="togglePlay"
            >
              <svg v-if="!playing" viewBox="0 0 24 24" class="size-5 ml-0.5" fill="currentColor" aria-hidden="true">
                <path d="M8 5v14l11-7z" />
              </svg>
              <svg v-else viewBox="0 0 24 24" class="size-5" fill="currentColor" aria-hidden="true">
                <path d="M7 5h4v14H7zM13 5h4v14h-4z" />
              </svg>
            </button>
            <button
              type="button"
              class="inline-flex items-center rounded-full border border-white/14 bg-white/8 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/14"
              @click="jumpBy(-10)"
            >
              后退 10 秒
            </button>
            <button
              type="button"
              class="inline-flex items-center rounded-full border border-white/14 bg-white/8 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/14"
              @click="jumpBy(10)"
            >
              前进 10 秒
            </button>
            <span class="text-sm text-slate-200">{{ playing ? "正在讲解" : "已暂停" }}</span>
          </div>

          <audio
            ref="audioRef"
            class="hidden"
            preload="metadata"
            :src="audioSrc"
            @play="playing = true"
            @pause="playing = false"
            @ended="onEnded"
            @timeupdate="onTimeUpdate"
            @loadedmetadata="onLoadedMetadata"
          >
            您的浏览器不支持音频播放。
          </audio>
        </div>
      </div>

    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = withDefaults(defineProps<{
  title?: string;
  script?: string;
  videoSrc?: string;
  audioSrc?: string;
  phase?: string;
  videoSource?: "jimeng_remote" | "jimeng_local_merge" | "fallback_local" | "audio_only" | "script_only" | "";
}>(), {
  title: "未命名主题",
  script: "",
  videoSrc: "",
  audioSrc: "",
  phase: "",
  videoSource: "",
});

const audioRef = ref<HTMLAudioElement | null>(null);
const playing = ref(false);
const currentTime = ref(0);
const duration = ref(0);

const hasVideo = computed(() => Boolean(props.videoSrc));
const hasAudio = computed(() => Boolean(props.audioSrc));
const isRemoteVideo = computed(() => props.videoSource === "jimeng_remote" || props.videoSource === "jimeng_local_merge");
const isFallbackVideo = computed(() => props.videoSource === "fallback_local");

const cues = computed(() => {
  const segments = (props.script || "")
    .split(/[\n。！？!?]/g)
    .map((item) => item.trim())
    .filter((item) => item.length >= 6);
  if (segments.length) return segments.slice(0, 6);
  return ["脚本已生成，系统正在整理适合课堂展示的讲解重点。"];
});

const keyPoints = computed(() => {
  const list = cues.value
    .map((item) => item.replace(/\s+/g, " ").trim())
    .filter(Boolean);
  const unique: string[] = [];
  for (const item of list) {
    if (!unique.includes(item)) unique.push(item);
    if (unique.length >= 4) break;
  }
  return unique.length ? unique : ["讲解内容已准备完成，等待画面与配音同步。"];
});

const cueIndex = computed(() => {
  if (!cues.value.length) return 0;
  if (!duration.value || !currentTime.value) return 0;
  return Math.min(cues.value.length - 1, Math.floor((currentTime.value / duration.value) * cues.value.length));
});

const currentCue = computed(() => cues.value[cueIndex.value] || cues.value[0]);
const progress = computed(() => {
  if (!duration.value) return 0;
  return Math.max(0, Math.min(100, (currentTime.value / duration.value) * 100));
});

const stageStatus = computed(() => {
  if (isFallbackVideo.value) return "备用画面已经准备好";
  if (isRemoteVideo.value) return "微课视频已经准备好";
  if (hasAudio.value) return "配音已完成";
  const phase = (props.phase || "").trim().toLowerCase();
  if (phase === "script") return "脚本生成中";
  if (phase === "video") return "视频画面生成中";
  if (phase === "video_pending") return "正在补充课堂画面";
  if (phase === "audio") return "配音合成中";
  return "内容整理中";
});

const modeBadgeText = computed(() => {
  if (isFallbackVideo.value) return "备用成片";
  if (hasVideo.value) return "微课成片";
  if (hasAudio.value) return "演示模式";
  return "脚本预览";
});

const heroDescription = computed(() => {
  if (props.videoSource === "jimeng_remote") return "课堂画面已经准备好，现在可以直接预览整段视频。";
  if (props.videoSource === "jimeng_local_merge") return "画面和配音已经合成完成，现在播放的是可直接回看的完整版本。";
  if (isFallbackVideo.value) return "本次先为你准备了可播放的备用画面，脚本和配音仍可正常使用。";
  if (hasAudio.value) return "现在可以先边听配音边看重点字幕，完整画面准备好后会继续补上。";
  return "脚本已经生成，系统正在准备画面或配音。";
});

const availabilityText = computed(() => {
  if (hasVideo.value) return "视频可播放";
  if (hasAudio.value) return "音频可播放";
  return "内容处理中";
});

const sourceBadgeText = computed(() => {
  if (props.videoSource === "jimeng_remote") return "课堂视频";
  if (props.videoSource === "jimeng_local_merge") return "完整合成版";
  if (isFallbackVideo.value) return "备用展示版";
  if (hasAudio.value) return "动态字幕演示";
  return "等待画面生成";
});

const formatTime = (seconds: number) => {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const minute = Math.floor(safe / 60);
  const second = Math.floor(safe % 60);
  return `${minute}:${second.toString().padStart(2, "0")}`;
};

const togglePlay = async () => {
  if (!audioRef.value) return;
  try {
    if (playing.value) audioRef.value.pause();
    else await audioRef.value.play();
  } catch {
    playing.value = false;
  }
};

const jumpBy = (offset: number) => {
  if (!audioRef.value) return;
  audioRef.value.currentTime = Math.max(0, Math.min(duration.value || 0, audioRef.value.currentTime + offset));
};

const seekAudio = (event: MouseEvent) => {
  if (!audioRef.value || !duration.value) return;
  const target = event.currentTarget as HTMLDivElement | null;
  if (!target) return;
  const rect = target.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  audioRef.value.currentTime = ratio * duration.value;
};

const onTimeUpdate = () => {
  if (!audioRef.value) return;
  currentTime.value = audioRef.value.currentTime || 0;
};

const onLoadedMetadata = () => {
  if (!audioRef.value) return;
  duration.value = audioRef.value.duration || 0;
};

const onEnded = () => {
  playing.value = false;
  currentTime.value = 0;
};

watch(
  () => props.audioSrc,
  () => {
    if (audioRef.value) {
      audioRef.value.pause();
      audioRef.value.load();
    }
    playing.value = false;
    currentTime.value = 0;
    duration.value = 0;
  }
);
</script>

<style scoped>
.teaching-stage-orb {
  position: absolute;
  border-radius: 9999px;
  filter: blur(6px);
  opacity: 0.7;
  animation: teachingStageFloat 12s ease-in-out infinite;
}

.teaching-stage-orb-a {
  inset: auto auto 18% 8%;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.42), transparent 68%);
}

.teaching-stage-orb-b {
  inset: 12% 9% auto auto;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.44), transparent 68%);
  animation-delay: -4s;
}

.teaching-stage-pulse {
  animation: teachingStagePulse 1.4s ease-in-out infinite;
}

@keyframes teachingStageFloat {
  0%, 100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(0, -14px, 0) scale(1.05);
  }
}

@keyframes teachingStagePulse {
  0%, 100% {
    transform: scale(0.85);
    opacity: 0.45;
  }
  50% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
