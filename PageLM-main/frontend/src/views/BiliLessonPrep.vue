<template>
  <div class="min-h-screen w-full px-4 md:pl-60 md:pr-6 lg:pl-64 lg:pr-10 pb-16">
    <div class="w-full max-w-6xl mx-auto mt-20 lg:mt-8">
      <header class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-6 shadow-[0_14px_34px_rgba(15,23,42,0.14)]">
        <div class="flex items-start gap-3">
          <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-400 border border-sky-400/30 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 6.5A2.5 2.5 0 0 1 7.5 4h9A2.5 2.5 0 0 1 19 6.5v11A2.5 2.5 0 0 1 16.5 20h-9A2.5 2.5 0 0 1 5 17.5v-11Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="m10 9 5 3-5 3V9Z" />
            </svg>
          </span>
          <div>
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">bilibili视频备课</h1>
            <p class="mt-1 text-sm text-[color:var(--nav-text-muted)]">输入课题与教学场景即可检索B站备课视频，快速定位导入素材、重难点讲解与课堂案例。</p>
          </div>
        </div>

        <div class="mt-5 flex flex-col sm:flex-row gap-3">
          <label for="bili-prep-keyword" class="sr-only">输入备课关键词</label>
          <input
            id="bili-prep-keyword"
            v-model="keyword"
            type="text"
            placeholder="例如：高中数学 函数单调性 课堂导入"
            class="w-full rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)] px-4 py-3 text-[color:var(--app-text)] placeholder:text-[color:var(--nav-text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/60"
            @keydown.enter="onSearch"
          />
          <button
            type="button"
            class="rounded-2xl px-5 py-3 bg-gradient-to-r from-sky-400 to-cyan-400 text-slate-950 font-semibold border border-sky-300/70 shadow-[0_12px_24px_rgba(56,189,248,0.32)] hover:brightness-110 transition-all duration-200 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="loading"
            @click="onSearch"
          >
            {{ loading ? "检索中..." : "检索备课视频" }}
          </button>
        </div>
      </header>

      <section class="mt-6">
        <p v-if="error" class="rounded-2xl border border-rose-300/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {{ error }}
        </p>

        <div v-if="!hasSearched" class="space-y-6">
          <div class="rounded-[32px] border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.15)]">
            <div class="flex items-center gap-2 mb-4">
              <span class="text-[10px] px-2.5 py-1 rounded-full bg-sky-400/15 border border-sky-300/40 text-sky-200">LESSON</span>
              <h2 class="text-lg font-semibold text-[color:var(--app-text)]">备课检索特点</h2>
            </div>
            <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <article class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/70 p-5 shadow-[0_10px_24px_rgba(15,23,42,0.12)]">
                <div class="text-[15px] font-semibold text-[color:var(--app-text)]">课题关键词直达</div>
                <p class="mt-2 text-sm leading-6 text-[color:var(--nav-text-muted)]">围绕章节、课标与重难点检索视频，快速形成备课素材池。</p>
              </article>
              <article class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/70 p-5 shadow-[0_10px_24px_rgba(15,23,42,0.12)]">
                <div class="text-[15px] font-semibold text-[color:var(--app-text)]">课程信息清晰</div>
                <p class="mt-2 text-sm leading-6 text-[color:var(--nav-text-muted)]">同步展示标题、UP主、时长、BV号，便于快速判断课堂适配度。</p>
              </article>
              <article class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/70 p-5 shadow-[0_10px_24px_rgba(15,23,42,0.12)]">
                <div class="text-[15px] font-semibold text-[color:var(--app-text)]">备课场景覆盖</div>
                <p class="mt-2 text-sm leading-6 text-[color:var(--nav-text-muted)]">可检索导入视频、知识讲解、实验演示、习题讲评等多种场景内容。</p>
              </article>
            </div>
          </div>

          <div class="rounded-[28px] border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.14)]">
            <div class="text-sm text-[color:var(--nav-text-muted)]">备课关键词建议：</div>
            <div class="mt-3 flex flex-wrap gap-2">
              <button type="button" class="px-3.5 py-2 rounded-full border border-sky-300/40 bg-sky-400/10 text-sm font-medium text-[color:var(--app-text)] hover:bg-sky-400/20 transition-colors duration-200 cursor-pointer" @click="useKeyword('高中数学 函数单调性 导入')">高中数学 函数单调性 导入</button>
              <button type="button" class="px-3.5 py-2 rounded-full border border-sky-300/40 bg-sky-400/10 text-sm font-medium text-[color:var(--app-text)] hover:bg-sky-400/20 transition-colors duration-200 cursor-pointer" @click="useKeyword('初中物理 压强 实验课')">初中物理 压强 实验课</button>
              <button type="button" class="px-3.5 py-2 rounded-full border border-sky-300/40 bg-sky-400/10 text-sm font-medium text-[color:var(--app-text)] hover:bg-sky-400/20 transition-colors duration-200 cursor-pointer" @click="useKeyword('语文 古诗词 鉴赏 课堂')">语文 古诗词 鉴赏 课堂</button>
              <button type="button" class="px-3.5 py-2 rounded-full border border-sky-300/40 bg-sky-400/10 text-sm font-medium text-[color:var(--app-text)] hover:bg-sky-400/20 transition-colors duration-200 cursor-pointer" @click="useKeyword('化学 氧化还原 重难点')">化学 氧化还原 重难点</button>
            </div>
          </div>
        </div>

        <div v-else-if="!loading && !error && videos.length === 0" class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-8 text-center text-[color:var(--nav-text-muted)]">
          未找到相关备课视频，请调整关键词重试。
        </div>

        <div v-else class="space-y-4">
          <div class="flex items-center justify-between rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 px-4 py-3">
            <div class="text-sm text-[color:var(--nav-text-muted)]">共找到 {{ videos.length }} 条备课视频结果</div>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)] px-3.5 py-2 text-sm font-semibold text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg)] transition-colors duration-200 cursor-pointer"
              @click="backToLanding"
            >
              <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="m15 18-6-6 6-6" />
              </svg>
              返回重新检索
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
            <article
              v-for="video in videos"
              :key="video.bvid + video.title"
              class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 overflow-hidden shadow-[0_14px_30px_rgba(15,23,42,0.14)] hover:shadow-[0_18px_32px_rgba(15,23,42,0.2)] transition-shadow duration-200"
            >
              <div class="aspect-video bg-[color:var(--nav-bg)] overflow-hidden">
                <img
                  :src="resolvedCover(video)"
                  :alt="video.title"
                  referrerpolicy="no-referrer"
                  class="w-full h-full object-cover"
                  @error="onCoverError"
                />
              </div>

              <div class="p-4">
                <h3 class="text-[15px] font-semibold text-[color:var(--app-text)] overflow-hidden text-ellipsis whitespace-nowrap" :title="video.title">
                  {{ video.title || "未命名视频" }}
                </h3>
                <p class="mt-2 text-sm text-[color:var(--nav-text-muted)]">UP主：{{ video.author || "未知" }}</p>
                <p class="text-sm text-[color:var(--nav-text-muted)]">时长：{{ video.duration || "--" }}</p>

                <button
                  type="button"
                  class="mt-4 w-full rounded-xl border border-sky-300/50 bg-sky-400/20 text-slate-950 py-2.5 font-black hover:bg-sky-400/30 transition-colors duration-200 cursor-pointer"
                  @click="openVideo(video.bvid)"
                >
                  点击查看备课
                </button>
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { err, searchBilibiliVideos, type BilibiliVideoItem } from "../lib/api";

const keyword = ref("");
const loading = ref(false);
const error = ref("");
const videos = ref<BilibiliVideoItem[]>([]);
const hasSearched = ref(false);

const onSearch = async () => {
  const q = keyword.value.trim();
  if (!q) {
    error.value = "请输入备课关键词后再检索。";
    videos.value = [];
    return;
  }

  hasSearched.value = true;
  loading.value = true;
  error.value = "";

  try {
    const data = await searchBilibiliVideos(q);
    videos.value = data.items || [];
  } catch (e) {
    videos.value = [];
    error.value = `检索失败：${err(e)}`;
  } finally {
    loading.value = false;
  }
};

const useKeyword = (value: string) => {
  keyword.value = value;
  onSearch();
};

const backToLanding = () => {
  hasSearched.value = false;
  videos.value = [];
  error.value = "";
};

const fallbackCover = (title: string) =>
  `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#dbeafe" />
          <stop offset="100%" stop-color="#bfdbfe" />
        </linearGradient>
      </defs>
      <rect width="640" height="360" rx="28" fill="url(#g)" />
      <text x="320" y="170" text-anchor="middle" font-size="28" font-family="PingFang SC, Microsoft YaHei, sans-serif" fill="#0f172a">Bilibili 备课视频</text>
      <text x="320" y="214" text-anchor="middle" font-size="18" font-family="PingFang SC, Microsoft YaHei, sans-serif" fill="#334155">${title || "暂无封面"}</text>
    </svg>`
  )}`;

const resolvedCover = (video: BilibiliVideoItem) => {
  const cover = (video.cover || "").trim();
  if (!cover) return fallbackCover(video.title || "暂无封面");
  if (cover.startsWith("//")) return `https:${cover}`;
  if (cover.startsWith("http://")) return `https://${cover.slice("http://".length)}`;
  return cover;
};

const onCoverError = (event: Event) => {
  const target = event.target as HTMLImageElement | null;
  if (!target) return;
  target.src = fallbackCover(target.alt || "暂无封面");
};

const openVideo = (bvid: string) => {
  if (!bvid) return;
  window.open(`https://www.bilibili.com/video/${bvid}`, "_blank", "noopener,noreferrer");
};
</script>
