<template>
  <div class="group rounded-2xl bg-stone-950 border border-zinc-800 p-4 hover:border-fuchsia-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-fuchsia-500/10">
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <div class="text-xs uppercase tracking-wide text-fuchsia-400 font-semibold">播客生成器</div>
          <div class="w-2 h-2 rounded-full bg-gradient-to-r from-fuchsia-400 to-rose-400 animate-pulse"></div>
        </div>
        <div class="text-white font-semibold text-xl mb-2">AI 播客</div>
        <div class="text-stone-300 text-sm leading-relaxed">
          从任何主题或笔记生成引人入胜的播客。非常适合随时随地学习。
        </div>
      </div>
    </div>

    <div class="mt-6 space-y-3">
      <div class="flex gap-2">
        <div class="relative flex-1">
          <input
            v-model="topic"
            placeholder="输入主题或粘贴笔记..."
            class="w-full px-4 py-3 pr-16 rounded-xl bg-stone-900/70 border border-zinc-700 text-white placeholder-zinc-400 focus:border-fuchsia-500 focus:ring-2 focus:ring-fuchsia-500/20 outline-none transition-all duration-300"
            @keydown.enter.exact.prevent="onGenerate"
          />
        </div>
        <button
          type="button"
          @click="onGenerate"
          :disabled="busy || !topic.trim()"
          class="px-6 py-3 rounded-xl bg-gradient-to-r from-fuchsia-500 to-rose-500 hover:from-fuchsia-600 hover:to-rose-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-all duration-300"
        >
          {{ busy ? "生成中…" : "生成" }}
        </button>
      </div>

      <div v-if="status" class="p-4 rounded-xl bg-fuchsia-950/40 border border-fuchsia-800/40 text-fuchsia-200 font-medium">
        {{ status }}
        <div class="text-xs mt-2 opacity-70">
          音频文件: {{ audioFile ? "已设置" : "未设置" }} | 忙碌中: {{ busy ? "是" : "否" }}
        </div>
      </div>

      <div v-if="audioFile" class="space-y-3">
        <div class="p-4 rounded-xl bg-stone-900/70 border border-zinc-700">
          <div class="text-sm text-stone-400 mb-2">预览:</div>
          <audio controls class="w-full" :src="audioFile">您的浏览器不支持音频元素。</audio>
        </div>

        <a
          :href="audioFile"
          :download="audioFilename || 'podcast.mp3'"
          class="block p-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-medium text-center transition-all duration-300 shadow-lg hover:shadow-emerald-500/20"
        >
          下载播客
        </a>
      </div>

      <div v-if="!audioFile && !busy" class="text-xs text-stone-500 text-center p-2">
        点击生成按钮创建播客
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { podcastStart, connectPodcastStream, getPodcastDetail, type PodcastEvent } from "../../lib/api";
import { env } from "../../config/env";
import { getAuthToken } from "../../lib/auth";
import { getRouteState } from "../../lib/routerState";

const route = useRoute();
const topic = ref("");
const busy = ref(false);
const status = ref("");
const audioFile = ref<string | null>(null);
const audioFilename = ref<string | null>(null);
const currentPid = ref<string>("");

let activeClose: null | (() => void) = null;
let timeoutId: number | null = null;

const cleanup = () => {
  if (timeoutId) window.clearTimeout(timeoutId);
  timeoutId = null;
  if (activeClose) activeClose();
  activeClose = null;
};

const resolveBackendMediaUrl = (raw?: string | null) => {
  if (!raw) return null;
  const value = String(raw).trim();
  if (!value) return null;
  try {
    const parsed = new URL(value, env.backend);
    return parsed.toString();
  } catch {
    return value;
  }
};

const withDownloadToken = (raw?: string | null) => {
  const resolved = resolveBackendMediaUrl(raw);
  if (!resolved) return null;
  try {
    const parsed = new URL(resolved, env.backend);
    if (!parsed.pathname.includes("/podcast/download/")) return parsed.toString();
    const token = getAuthToken();
    if (token) parsed.searchParams.set("token", token);
    return parsed.toString();
  } catch {
    return resolved;
  }
};

const fetchPodcastResult = async (pid: string) => {
  if (!pid) return;
  try {
    const res = await getPodcastDetail(pid);
    if (!res?.ok) return;
    const media = withDownloadToken(res.podcast?.static || res.podcast?.file || null);
    if (media) {
      audioFile.value = media;
      const fileName = (res.podcast?.file || res.podcast?.static || "").split("/").pop();
      audioFilename.value = fileName || "podcast.mp3";
      status.value = "就绪 - 音频文件已准备好！";
      return;
    }
    if (res.podcast?.status === "ready" && res.script) {
      status.value = "脚本已生成，音频尚未准备好";
    } else if (res.podcast?.status === "error") {
      status.value = `错误: ${res.podcast.error || "生成失败"}`;
    }
  } catch {
    return;
  }
};

const connectStream = (pid: string) => {
  cleanup();
  currentPid.value = pid;
  const { close } = connectPodcastStream(pid, (ev: PodcastEvent) => {
    if (ev.type === "ready") status.value = "已连接，正在生成…";
    if (ev.type === "phase") status.value = `状态: ${ev.value}`;
    if (ev.type === "script") status.value = "脚本已生成，正在创建音频…";
    if (ev.type === "audio") {
      const audioUrl = withDownloadToken(ev.staticUrl || ev.file || "") || "";
      audioFile.value = audioUrl;
      audioFilename.value = ev.filename || "podcast.mp3";
      status.value = "就绪 - 音频文件已准备好！";
    }
    if (ev.type === "done") {
      void fetchPodcastResult(pid);
      status.value = "完成";
      busy.value = false;
      setTimeout(() => close(), 1000);
    }
    if (ev.type === "error") {
      status.value = `错误: ${ev.error}`;
      close();
      busy.value = false;
    }
    if (ev.type === "close" && busy.value) {
      void fetchPodcastResult(pid);
    }
  });
  activeClose = close;
  timeoutId = window.setTimeout(() => {
    status.value = "错误: 超时 - 生成时间过长";
    busy.value = false;
    close();
  }, 120000);
};

const onGenerate = async () => {
  if (!topic.value.trim() || busy.value) return;
  busy.value = true;
  status.value = "正在启动…";
  audioFile.value = null;
  audioFilename.value = null;

  try {
    const { pid } = await podcastStart({ topic: topic.value });
    currentPid.value = pid;
    await new Promise((resolve) => setTimeout(resolve, 100));
    connectStream(pid);
  } catch (e: any) {
    status.value = e?.message || "失败";
    busy.value = false;
  }
};

const handleRouteState = () => {
  const state = getRouteState<{ podcastPid?: string; podcastTopic?: string }>();
  if (!state?.podcastPid) return;
  currentPid.value = state.podcastPid;
  topic.value = state.podcastTopic || "";
  busy.value = true;
  status.value = "正在连接播客生成器…";
  connectStream(state.podcastPid);
};

onMounted(() => {
  handleRouteState();
});

watch(
  () => route.fullPath,
  () => handleRouteState()
);

onBeforeUnmount(() => {
  cleanup();
});
</script>
