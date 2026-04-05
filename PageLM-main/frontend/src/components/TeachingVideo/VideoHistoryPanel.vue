<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-violet-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7">
            <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
        </span>
        历史视频
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-lg hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewVideo"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建视频
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="videos.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="video in videos" :key="video.id" class="min-w-0">
        <div class="flex items-stretch gap-1.5">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
            @click="openVideo(video.id)"
            :title="video.title || '未命名视频'"
          >
            <div class="truncate">{{ video.title || "未命名视频" }}</div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="openPreview(video.id)"
            aria-label="预览视频"
            title="预览"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-violet-300" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removeVideo(video.id)"
            aria-label="删除视频"
            title="删除"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
            </svg>
          </button>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史视频</div>

    <!-- 预览弹层：点击预览后弹出，可播放视频 -->
    <Teleport to="body">
      <div
        v-if="previewVideoId"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        @click.self="closePreview"
      >
        <div class="relative w-full max-w-3xl rounded-2xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-2xl overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3 border-b border-[color:var(--glass-border)]">
            <span class="text-sm font-semibold text-[color:var(--app-text)]">视频预览（有声版）</span>
            <button
              type="button"
              class="rounded-xl p-2 text-[color:var(--nav-text-muted)] hover:bg-[color:var(--nav-hover-bg)] hover:text-[color:var(--app-text)] transition-colors"
              aria-label="关闭"
              @click="closePreview"
            >
              <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="p-4">
            <video
              :key="previewVideoId"
              :src="previewVideoUrl"
              controls
              class="w-full rounded-xl bg-black aspect-video"
              playsinline
            />
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup lang="ts">
import { type Ref, computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { env } from "../../config/env";
import { getAuthToken } from "../../lib/auth";
import { deleteTeachingVideo, getTeachingVideoDetail, listTeachingVideos } from "../../lib/api";

const router = useRouter();
const videoRole = inject<Ref<"student" | "teacher">>("videoRole");
const videoBasePath = inject<Ref<string>>("videoBasePath");

const loading = ref(false);
const videos = ref<{ id: string; title?: string; at?: number }[]>([]);
const previewVideoId = ref<string | null>(null);
/** 预览时优先使用有声版（本地合成）URL */
const previewLocalVideoUrl = ref("");

const role = () => videoRole?.value ?? "teacher";
const basePath = () => videoBasePath?.value ?? "/teaching-video";

const previewVideoUrl = computed(() => {
  const id = previewVideoId.value;
  if (!id) return "";
  if (previewLocalVideoUrl.value) return previewLocalVideoUrl.value;
  const base = `${env.backend}/teaching-videos/${id}/video`;
  try {
    const token = getAuthToken();
    if (!token) return base;
    const parsed = new URL(base);
    parsed.searchParams.set("token", token);
    return parsed.toString();
  } catch {
    return base;
  }
});

const loadVideos = async () => {
  loading.value = true;
  try {
    const res = await listTeachingVideos(role());
    videos.value = Array.isArray(res?.videos) ? res.videos : [];
  } catch {
    videos.value = [];
  } finally {
    loading.value = false;
  }
};

const openVideo = (id: string) => {
  if (!id) return;
  const currentId = router.currentRoute.value.query.videoId as string;
  if (currentId === id) {
    router.replace({ path: basePath() }).then(() => {
      router.push({ path: basePath(), query: { videoId: id, t: String(Date.now()) }, state: { videoId: id } });
    });
    return;
  }
  router.push({ path: basePath(), query: { videoId: id, t: String(Date.now()) }, state: { videoId: id } });
};

const openPreview = async (id: string) => {
  if (!id) return;
  previewVideoId.value = id;
  previewLocalVideoUrl.value = "";
  try {
    const res = await getTeachingVideoDetail(id);
    if (res?.ok && res.localVideoUrl) {
      try {
        previewLocalVideoUrl.value = new URL(res.localVideoUrl, env.backend).toString();
      } catch {
        previewLocalVideoUrl.value = res.localVideoUrl;
      }
    }
  } catch {
    // 无有声版时使用代理流
  }
};

const closePreview = () => {
  previewVideoId.value = null;
  previewLocalVideoUrl.value = "";
};

const startNewVideo = () => {
  router.push({ path: basePath(), query: { new: String(Date.now()) } });
};

const removeVideo = async (id: string) => {
  if (!id) return;
  if (!window.confirm("确定删除该教学视频吗？")) return;
  const prev = videos.value;
  videos.value = prev.filter((item) => item.id !== id);
  try {
    await deleteTeachingVideo(id);
    if ((router.currentRoute.value.query.videoId as string) === id) {
      router.push({ path: basePath() });
    }
    if (previewVideoId.value === id) closePreview();
    await loadVideos();
  } catch {
    videos.value = prev;
  }
};

onMounted(loadVideos);
watch(() => videoRole?.value, () => loadVideos());

onMounted(() => {
  window.addEventListener("teaching-video:updated", loadVideos as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("teaching-video:updated", loadVideos as EventListener);
});
</script>
