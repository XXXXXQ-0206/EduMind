<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 8.25h15v7.5h-15z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12" />
          </svg>
        </span>
        历史播客
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewPodcast"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建播客
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="podcasts.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="item in podcasts" :key="item.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
            @click="openPodcast(item.id)"
            @contextmenu.prevent="openContextMenu($event, item)"
            :title="item.title || '未命名播客'"
          >
            <div class="truncate">{{ item.title || "未命名播客" }}</div>
            <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-[color:var(--nav-text-muted)]">
              <span>{{ formatTime(item.at) }}</span>
              <span>·</span>
              <span>{{ lengthLabel(item.length) }}</span>
              <span
                class="rounded-full border px-1.5 py-0.5 font-semibold"
                :class="podcastStatusTone(item)"
              >
                {{ podcastStatusLabel(item) }}
              </span>
            </div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="toggleDetails(item.id)"
            aria-label="查看播客详情"
            :title="'查看播客详情'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removePodcast(item.id)"
            aria-label="删除播客"
            :title="'删除播客'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
        <div v-if="expandedId === item.id" class="mt-3 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-3 space-y-3 max-h-80 overflow-y-auto custom-scroll">
          <div v-if="details[item.id]" class="space-y-2">
            <div class="text-xs text-[color:var(--nav-text-muted)]">摘要</div>
            <div class="text-xs text-[color:var(--app-text)] whitespace-pre-wrap">{{ details[item.id].summary || '暂无摘要' }}</div>
            <div v-if="details[item.id].segments?.length" class="pt-2">
              <div class="text-xs text-[color:var(--nav-text-muted)]">片段预览</div>
              <ul class="mt-2 space-y-1">
                <li
                  v-for="(seg, i) in (details[item.id].segments ?? []).slice(0, 4)"
                  :key="i"
                  class="text-xs text-[color:var(--app-text)]"
                >
                  <div class="font-semibold">{{ seg.spk === 'A' ? '主持人 A' : '主持人 B' }}</div>
                  <div class="text-[color:var(--nav-text-muted)] line-clamp-2">{{ seg.md }}</div>
                </li>
              </ul>
              <div v-if="(details[item.id].segments ?? []).length > 4" class="text-[10px] text-[color:var(--nav-text-muted)] mt-1">…还有 {{ (details[item.id].segments ?? []).length - 4 }} 个片段</div>
            </div>
            <!-- 内联音频播放器 -->
            <div v-if="podcastFile(item.id)" class="pt-2">
              <div class="text-xs text-[color:var(--nav-text-muted)] mb-2">音频预览</div>
              <audio
                class="w-full h-8"
                controls
                preload="none"
                :src="podcastFile(item.id)"
              >您的浏览器不支持音频播放。</audio>
            </div>
            <div class="flex items-center gap-3 pt-1">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 text-xs text-sky-300 hover:text-sky-200 transition-colors"
                @click.stop="openPodcast(item.id)"
              >
                <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                打开详情
              </button>
              <a
                v-if="podcastFile(item.id)"
                :href="podcastFile(item.id)"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 text-xs text-emerald-300 hover:text-emerald-200 transition-colors"
              >
                <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                </svg>
                下载音频
              </a>
            </div>
          </div>
          <div v-else-if="item.status === 'error'" class="text-xs text-rose-300">
            {{ friendlyPodcastMessage(item.error) }}
          </div>
          <div v-else-if="item.status === 'pending' || item.status === 'generating'" class="text-xs text-[color:var(--nav-text-muted)]">
            当前播客仍在处理中，点击条目会回到等待页继续拉取状态。
          </div>
          <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无播客详情</div>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史播客</div>
    <HistoryContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="closeContextMenu"
      @select="addPodcastToBag"
    />
  </aside>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deletePodcast, friendlyTaskMessage, getPodcastDetail, listPodcasts, type PodcastMeta, type PodcastScript } from "../../lib/api";
import { addLearningBagRecord } from "../../lib/learningBag";
import HistoryContextMenu from "../common/HistoryContextMenu.vue";

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const podcasts = ref<PodcastMeta[]>([]);
const expandedId = ref<string | null>(null);
const details = ref<Record<string, PodcastScript>>({});
const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextTarget = ref<{ id: string; title?: string; at?: number } | null>(null);

const loadPodcasts = async () => {
  loading.value = true;
  try {
    const res = await listPodcasts();
    podcasts.value = Array.isArray(res?.podcasts) ? res.podcasts : [];
  } catch {
    podcasts.value = [];
  } finally {
    loading.value = false;
  }
};

const openPodcast = (id: string) => {
  if (!id) return;
  // 使用时间戳确保即使是同一个 pid 也能触发路由变化
  const currentPid = route.query.pid as string;
  if (currentPid === id) {
    // 同一个 pid，先导航到空状态再跳回
    router.replace({ path: "/podcast" }).then(() => {
      router.push({ path: "/podcast", query: { pid: id, t: String(Date.now()) }, state: { pid: id } });
    });
  } else {
    router.push({ path: "/podcast", query: { pid: id, t: String(Date.now()) }, state: { pid: id } });
  }
};

const startNewPodcast = () => {
  router.push({ path: "/podcast", query: { new: String(Date.now()) } });
};

const openContextMenu = (event: MouseEvent, podcast: { id: string; title?: string; at?: number }) => {
  contextTarget.value = podcast;
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

const addPodcastToBag = () => {
  const podcast = contextTarget.value;
  if (!podcast?.id) return;
  addLearningBagRecord({
    type: "podcast",
    refId: podcast.id,
    title: podcast.title || "未命名播客",
    subtitle: formatTime(podcast.at),
    path: "/podcast",
    query: { pid: podcast.id },
  });
};

const toggleDetails = async (id: string) => {
  if (!id) return;
  if (expandedId.value === id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = id;
  if (!details.value[id]) {
    try {
      const res = await getPodcastDetail(id);
      if (res?.ok && res.script) {
        details.value = { ...details.value, [id]: res.script };
      }
    } catch {
      return;
    }
  }
};

const podcastFile = (id: string) => {
  const hit = podcasts.value.find((item) => item.id === id);
  return hit?.file || hit?.static || "";
};

const removePodcast = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该播客吗？");
  if (!ok) return;
  const prev = podcasts.value;
  podcasts.value = prev.filter((item) => item.id !== id);
  try {
    await deletePodcast(id);
    if ((route.query.pid as string) === id) {
      router.push({ path: "/podcast" });
    }
    await loadPodcasts();
  } catch {
    podcasts.value = prev;
  }
};

const lengthLabel = (value?: string) => {
  if (value === "short") return "短";
  if (value === "long") return "长";
  return "中";
};

const podcastStatusLabel = (item: PodcastMeta) => {
  if (item.status === "ready") return "已完成";
  if (item.status === "error") return "失败";
  if (item.status === "generating") return "合成中";
  return "生成中";
};

const podcastStatusTone = (item: PodcastMeta) => {
  if (item.status === "ready") return "border-emerald-300/50 bg-emerald-100/70 text-emerald-700";
  if (item.status === "error") return "border-rose-300/50 bg-rose-100/70 text-rose-700";
  if (item.status === "generating") return "border-sky-300/50 bg-sky-100/70 text-sky-700";
  return "border-amber-300/50 bg-amber-100/70 text-amber-800";
};

const friendlyPodcastMessage = (value?: string) =>
  friendlyTaskMessage(value, {
    feature: "podcast",
    fallback: "这条播客暂时还没有准备好，请稍后再试。",
  });

const formatTime = (value?: number) => {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
};

const onUpdated = () => {
  loadPodcasts();
};

onMounted(() => {
  loadPodcasts();
  window.addEventListener("podcast:updated", onUpdated as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("podcast:updated", onUpdated as EventListener);
});
</script>
