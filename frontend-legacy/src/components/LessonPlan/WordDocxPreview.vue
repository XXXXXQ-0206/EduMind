<template>
  <section class="word-preview-shell">
    <div class="word-preview-toolbar">
      <div class="min-w-0">
        <div class="text-sm font-semibold text-[color:var(--app-text)] truncate">{{ title || "Word 预览" }}</div>
        <div class="mt-1 text-xs text-[color:var(--nav-text-muted)]">{{ statusText }}</div>
      </div>
      <button
        type="button"
        class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/50 px-3 py-2 text-xs text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer disabled:opacity-50"
        :disabled="loading || !src"
        @click="renderPreview"
      >
        刷新预览
      </button>
    </div>

    <div class="word-preview-stage custom-scroll">
      <div v-if="loading" class="word-preview-state">正在加载 Word 预览...</div>
      <div v-else-if="error" class="word-preview-error">
        <div class="font-semibold">Word 预览加载失败</div>
        <div class="mt-1 text-xs">{{ error }}</div>
      </div>
      <div v-else-if="!src" class="word-preview-state">暂无可预览的 Word 文件</div>
      <div ref="previewRef" class="word-preview-document" :class="{ 'is-hidden': loading || error || !src }"></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { Options } from "docx-preview";

const props = defineProps<{
  src: string;
  title?: string;
}>();

const previewRef = ref<HTMLElement | null>(null);
const loading = ref(false);
const error = ref("");
const statusText = ref("等待生成 Word 文件");
let abortController: AbortController | null = null;
let renderToken = 0;

async function renderPreview() {
  const url = props.src;
  const container = previewRef.value;
  const token = ++renderToken;
  error.value = "";

  if (!container) return;
  container.innerHTML = "";
  if (!url) {
    statusText.value = "等待生成 Word 文件";
    return;
  }

  abortController?.abort();
  abortController = new AbortController();
  loading.value = true;
  statusText.value = "正在渲染 Word 文件";

  try {
    const response = await fetch(url, {
      signal: abortController.signal,
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`预览文件请求失败：${response.status}`);
    }

    const blob = await response.blob();
    if (token !== renderToken) return;
    container.innerHTML = "";

    const { renderAsync } = await import("docx-preview");
    const options: Partial<Options> = {
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      breakPages: true,
      renderHeaders: true,
      renderFooters: true,
      renderFootnotes: true,
      renderEndnotes: true,
      useBase64URL: true,
      className: "docx",
    };
    await renderAsync(blob, container, container, options);
    if (token !== renderToken) return;
    stabilizeRenderedTables(container);
    statusText.value = "已生成 Word 预览";
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") return;
    error.value = err instanceof Error ? err.message : "无法渲染 Word 文件";
    statusText.value = "预览失败";
  } finally {
    if (token === renderToken) {
      loading.value = false;
    }
  }
}

watch(
  () => props.src,
  async () => {
    await nextTick();
    await renderPreview();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  abortController?.abort();
  renderToken += 1;
});

function stabilizeRenderedTables(container: HTMLElement) {
  container.querySelectorAll<HTMLTableElement>("table").forEach((table) => {
    table.classList.add("word-preview-table");

    const cells = Array.from(table.querySelectorAll<HTMLTableCellElement>("td, th"));
    if (!cells.length) return;

    const hasVisibleBorder = cells.some((cell) => {
      const style = window.getComputedStyle(cell);
      return ["Top", "Right", "Bottom", "Left"].some((side) => {
        const width = Number.parseFloat(style.getPropertyValue(`border-${side.toLowerCase()}-width`));
        const borderStyle = style.getPropertyValue(`border-${side.toLowerCase()}-style`);
        return width > 0 && borderStyle !== "none" && borderStyle !== "hidden";
      });
    });

    if (!hasVisibleBorder) {
      table.classList.add("word-preview-table--fallback-border");
    }
  });
}
</script>

<style scoped>
.word-preview-shell {
  overflow: hidden;
  border: 1px solid var(--glass-border);
  border-radius: 18px;
  background: color-mix(in srgb, var(--glass-bg) 82%, transparent);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
}

.word-preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--glass-border);
  padding: 12px 14px;
  background: color-mix(in srgb, var(--nav-bg) 48%, transparent);
}

.word-preview-stage {
  min-height: 58vh;
  max-height: 74vh;
  overflow: auto;
  background:
    linear-gradient(45deg, rgba(148, 163, 184, 0.12) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(148, 163, 184, 0.12) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(148, 163, 184, 0.12) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(148, 163, 184, 0.12) 75%);
  background-color: color-mix(in srgb, var(--app-bg-2) 82%, #f8fafc 18%);
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
  padding: 24px 12px;
}

.word-preview-document {
  width: max-content;
  min-width: 100%;
}

.word-preview-document.is-hidden {
  display: none;
}

.word-preview-state,
.word-preview-error {
  margin: 48px auto;
  max-width: 360px;
  border: 1px solid var(--nav-border);
  border-radius: 16px;
  background: color-mix(in srgb, var(--nav-bg) 70%, transparent);
  padding: 18px;
  text-align: center;
  font-size: 13px;
  color: var(--nav-text-muted);
}

.word-preview-error {
  color: rgb(254, 202, 202);
}

:deep(.docx-wrapper) {
  background: transparent;
  padding: 0;
}

:deep(.docx-wrapper > section.docx) {
  margin: 0 auto 18px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.22);
}

:deep(.docx) {
  color: #111827;
}

:deep(.docx *) {
  box-sizing: border-box;
}

:deep(.docx table) {
  max-width: none;
  table-layout: fixed;
  border-collapse: collapse;
  border-spacing: 0;
}

:deep(.docx table.word-preview-table) {
  overflow: visible;
}

:deep(.docx table.word-preview-table--fallback-border) {
  border: 1px solid #111827;
}

:deep(.docx table.word-preview-table--fallback-border td),
:deep(.docx table.word-preview-table--fallback-border th) {
  border: 1px solid #111827;
}

:deep(.docx table td),
:deep(.docx table th) {
  min-width: 24px;
  max-width: none;
  vertical-align: top;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: pre-wrap;
}

:deep(.docx table td > *),
:deep(.docx table th > *) {
  max-width: 100%;
}
</style>
