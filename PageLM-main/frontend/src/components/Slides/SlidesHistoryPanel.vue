<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-violet-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 19.5h8M10 16.5v3M14 16.5v3" />
          </svg>
        </span>
        历史幻灯片
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5 cursor-pointer"
        @click="startNewSlides"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建幻灯片
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="slides.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="slide in slides" :key="slide.id" class="min-w-0">
        <div class="flex items-stretch gap-1.5">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 border border-[color:var(--nav-border)] transition-colors cursor-pointer"
            :class="slide.status === 'generating' ? 'opacity-90' : 'hover:bg-[color:var(--nav-hover-bg-strong)]'"
            @click="openSlides(slide)"
            :title="slide.title || '未命名幻灯片'"
          >
            <div class="truncate">{{ slide.title || "未命名幻灯片" }}</div>
            <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-[color:var(--nav-text-muted)]">
              <span>页数：{{ slide.pageCount ?? 10 }}</span>
              <span
                class="rounded-full border px-1.5 py-0.5 font-semibold"
                :class="slideStatusTone(slide)"
              >
                {{ slideStatusLabel(slide) }}
              </span>
            </div>
            <div v-if="slide.status === 'generating'" class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">
              正在整理内容，完成后就能查看。
            </div>
          </button>
          <button
            type="button"
            class="w-8 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 transition-colors inline-flex items-center justify-center cursor-pointer text-[color:var(--nav-text-muted)] hover:text-violet-400 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="预览"
            title="预览"
            :disabled="slide.status === 'generating'"
            @click.stop="openPreview(slide)"
          >
            <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-8 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center cursor-pointer"
            @click.stop="removeSlides(slide.id)"
            aria-label="删除幻灯片"
            title="删除"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史幻灯片</div>

    <!-- 历史项预览弹窗 -->
    <Teleport to="body">
      <div
        v-if="previewOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
        @click.self="previewOpen = false"
      >
        <div class="bg-[color:var(--app-bg)] rounded-3xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col border border-[color:var(--glass-border)]">
          <div class="flex items-center justify-between p-4 border-b border-[color:var(--nav-border)]">
            <h3 class="text-lg font-semibold text-[color:var(--app-text)] truncate pr-2">{{ previewTitle || "预览" }}</h3>
            <div class="flex items-center gap-2 shrink-0">
              <button
                v-if="previewSlideId"
                type="button"
                class="px-3 py-1.5 rounded-xl text-sm font-medium text-violet-600 hover:bg-violet-500/10 transition-colors cursor-pointer"
                @click="openInPage"
              >
                在页面中打开
              </button>
              <button type="button" class="rounded-xl p-2 text-[color:var(--nav-text-muted)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer" @click="previewOpen = false" aria-label="关闭">
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
          <div v-if="previewLoading" class="flex-1 flex items-center justify-center p-8 text-[color:var(--nav-text-muted)] text-sm">加载中…</div>
          <div v-else class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-for="(slide, idx) in previewSlides" :key="idx" class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--app-bg-2)] p-4">
              <h4 class="text-base font-semibold text-[color:var(--app-text)] mb-2">{{ slide.title }}</h4>
              <ul v-if="slide.bullets?.length" class="list-disc list-inside text-sm text-[color:var(--app-text)] space-y-1">
                <li v-for="(b, i) in slide.bullets" :key="i">{{ b }}</li>
              </ul>
              <img v-if="slide.imageUrl" :src="slide.imageUrl" :alt="slide.title" class="mt-3 rounded-xl max-h-36 object-cover w-full" />
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getSlideDetail, type SlideItem } from "../../lib/api";
import { getUserScopedStorageKey } from "../../lib/userStorage";

export type SlideRecord = {
  id: string;
  title?: string;
  pageCount?: number;
  at?: number;
  status?: "generating" | "ready";
};

const router = useRouter();
const loading = ref(false);
const slides = ref<SlideRecord[]>([]);
const previewOpen = ref(false);
const previewSlideId = ref<string | null>(null);
const previewTitle = ref("");
const previewSlides = ref<SlideItem[]>([]);
const previewLoading = ref(false);

const SLIDES_STORAGE_KEY = "pagelm-slides-history";
const scopedSlidesStorageKey = () => getUserScopedStorageKey(SLIDES_STORAGE_KEY);

const loadSlides = () => {
  loading.value = true;
  try {
    const raw = localStorage.getItem(scopedSlidesStorageKey());
    const parsed = raw ? (JSON.parse(raw) as SlideRecord[]) : [];
    slides.value = Array.isArray(parsed) ? parsed : [];
  } catch {
    slides.value = [];
  } finally {
    loading.value = false;
  }
};

const slideStatusLabel = (slide: SlideRecord) => (slide.status === "generating" ? "生成中" : "已完成");

const slideStatusTone = (slide: SlideRecord) => (
  slide.status === "generating"
    ? "border-amber-300/50 bg-amber-100/70 text-amber-800"
    : "border-emerald-300/50 bg-emerald-100/70 text-emerald-700"
);

const openSlides = (slide: SlideRecord) => {
  if (!slide.id || slide.status === "generating") return;
  router.push({ path: "/slides", query: { slideId: slide.id }, state: { slideId: slide.id } });
};

const openPreview = async (slide: SlideRecord) => {
  if (!slide.id || slide.status === "generating") return;
  previewSlideId.value = slide.id;
  previewOpen.value = true;
  previewTitle.value = "";
  previewSlides.value = [];
  previewLoading.value = true;
  try {
    const res = await getSlideDetail(slide.id);
    if (res.ok && res.slides) {
      previewTitle.value = res.slide?.title ?? "";
      previewSlides.value = res.slides;
    }
  } catch {
    previewSlides.value = [];
  } finally {
    previewLoading.value = false;
  }
};

const openInPage = () => {
  if (previewSlideId.value) {
    openSlides({ id: previewSlideId.value, status: "ready" });
  }
  previewOpen.value = false;
};

const startNewSlides = () => {
  router.push({ path: "/slides", query: { new: String(Date.now()) } });
};

const removeSlides = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该幻灯片吗？");
  if (!ok) return;
  const prev = slides.value;
  slides.value = prev.filter((item) => item.id !== id);
  try {
    const raw = localStorage.getItem(scopedSlidesStorageKey());
    const parsed = raw ? (JSON.parse(raw) as SlideRecord[]) : [];
    const next = parsed.filter((item) => item.id !== id);
    localStorage.setItem(scopedSlidesStorageKey(), JSON.stringify(next));
  } catch {
    slides.value = prev;
  }
};

onMounted(loadSlides);

defineExpose({ loadSlides });
</script>
