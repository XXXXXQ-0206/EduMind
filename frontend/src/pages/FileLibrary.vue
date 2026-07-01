<template>
  <div class="feature-shell">
    <div class="w-full max-w-6xl mx-auto pt-6 pb-14 px-2 lg:flex-1 lg:min-h-0 lg:py-6 lg:flex lg:flex-col">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <RouterLink
            :to="isTeacherPage ? '/teacher/chat' : '/'"
            class="p-2 rounded-xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer"
            aria-label="返回"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-[color:var(--nav-text)]" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
            </svg>
          </RouterLink>
          <div>
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">{{ pageTitle }}</h1>
            <p class="text-xs text-[color:var(--app-subtitle)]">{{ pageSubtitle }}</p>
          </div>
        </div>
        <button
          type="button"
          :class="[
            'px-4 py-2 rounded-xl border text-sm transition-all duration-200 cursor-pointer disabled:opacity-60 inline-flex items-center gap-2',
            isTeacherPage
              ? 'btn-teacher-primary border-transparent text-[#0f172a] hover:opacity-95'
              : 'rounded-2xl bg-gradient-to-r from-[#facc15] to-[#eab308] border-[#facc15] text-[#1f2937] hover:brightness-105 shadow-[0_10px_15px_-3px_rgba(234,179,8,0.18)]'
          ]"
          :disabled="uploading"
          @click="triggerPick"
        >
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
          </svg>
          {{ uploading ? "上传中..." : "上传文件" }}
        </button>
      </div>

      <!-- 上传文件：内含拖拽区、概览、教学/学习交互文件夹 -->
      <section
        class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 shadow-[0_8px_30px_rgba(0,0,0,0.08)] p-5 mb-6"
        @dragover.prevent="onDragOver"
        @dragleave="onDragLeave"
        @drop.prevent="onDrop"
      >
        <div class="flex items-center gap-2 mb-4">
          <span class="flex size-9 items-center justify-center rounded-xl bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--nav-text)]">
            <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
          </span>
          <span class="text-sm font-semibold text-[color:var(--app-text)]">上传文件</span>
        </div>
        <div
          class="rounded-2xl border border-dashed p-5 transition-colors duration-200"
          :class="isTeacherPage
            ? (dragActive ? 'bg-[var(--teacher-accent-soft)] border-[color:var(--teacher-primary-500)]' : 'border-[color:var(--teacher-primary-500)]/40 bg-[color:var(--app-bg-2)]/70')
            : (dragActive ? 'bg-[#fef3c7]/80 border-[#eab308]' : 'border-[#facc15]/50 bg-[color:var(--app-bg-2)]/70')"
        >
          <div class="flex flex-col md:flex-row md:items-center gap-4">
            <div class="size-12 rounded-xl border flex items-center justify-center shrink-0" :class="isTeacherPage ? 'bg-[var(--teacher-btn-gradient)] border-transparent' : 'bg-gradient-to-br from-[#fde68a] to-[#facc15] border-[#facc15]/60'">
              <svg viewBox="0 0 24 24" class="size-6" :class="isTeacherPage ? 'text-[#0f172a]' : 'text-[#92400e]'" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v11m0 0-3.5-3.5M12 15.5l3.5-3.5M6 19.5h12" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[color:var(--app-text)] font-medium">拖拽文件到这里或点击选择</div>
              <div class="text-xs text-[color:var(--nav-text-muted)] mt-1">支持 PDF、PPT、DOC、TXT、MD、图片与音频</div>
              <div class="text-xs text-[color:var(--nav-text-muted)]/90 mt-1">{{ uploadHint }}</div>
            </div>
            <button type="button" class="shrink-0 px-4 py-2 rounded-xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer disabled:opacity-60 inline-flex items-center gap-2 text-[color:var(--nav-text)] text-sm" :disabled="uploading" @click="triggerPick">
              <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v11m0 0-3.5-3.5M12 15.5l3.5-3.5M6 19.5h12" /></svg>
              选择文件
            </button>
          </div>
        </div>
        <div v-if="error" class="mt-3 text-xs text-red-600 dark:text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl px-3 py-2">{{ error }}</div>

        <!-- 概览：文件数、总容量、最近上传 -->
        <div class="grid grid-cols-3 gap-3 mt-4">
          <div class="rounded-xl bg-[color:var(--app-bg-2)]/80 border border-[color:var(--glass-border)] px-4 py-3">
            <div class="text-xs text-[color:var(--nav-text-muted)]">文件数量</div>
            <div class="text-lg font-semibold text-[color:var(--app-text)] mt-1">{{ totalCount }}</div>
          </div>
          <div class="rounded-xl bg-[color:var(--app-bg-2)]/80 border border-[color:var(--glass-border)] px-4 py-3">
            <div class="text-xs text-[color:var(--nav-text-muted)]">总容量</div>
            <div class="text-lg font-semibold text-[color:var(--app-text)] mt-1">{{ totalSize }}</div>
          </div>
          <div class="rounded-xl bg-[color:var(--app-bg-2)]/80 border border-[color:var(--glass-border)] px-4 py-3 min-w-0">
            <div class="text-xs text-[color:var(--nav-text-muted)]">最近上传</div>
            <div class="text-sm text-[color:var(--app-text)] mt-1 truncate" :title="latestLabel">{{ latestLabel }}</div>
          </div>
        </div>

        <!-- 教学/学习交互文件夹（置于上传框内） -->
        <div class="mt-4 pt-4 border-t border-[color:var(--glass-border)]">
          <div class="flex items-center justify-between gap-3 mb-2">
            <div class="flex items-center gap-2">
              <span class="flex size-8 items-center justify-center rounded-lg bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--nav-text)]">
                <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-2.12 0L2.25 15.75m13.5-6.75 2.12-2.12a1.5 1.5 0 0 1 2.12 0L21.75 15.75" /></svg>
              </span>
              <div>
                <div class="text-sm font-semibold text-[color:var(--app-text)]">{{ folderLabel }}</div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">{{ folderHint }}</div>
              </div>
            </div>
            <span class="text-xs text-[color:var(--nav-text-muted)] shrink-0">已选 {{ learningFolderFiles.length }} 个</span>
          </div>
          <div v-if="learningFolderFiles.length" class="space-y-2 max-h-40 overflow-y-auto rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/50 p-2">
            <div v-for="file in learningFolderFiles" :key="file.id" class="flex items-center justify-between gap-3 rounded-lg bg-[color:var(--glass-bg)]/60 border border-[color:var(--glass-border)] px-3 py-2">
              <div class="min-w-0 truncate text-sm text-[color:var(--app-text)]" :title="file.originalName">{{ file.originalName }}</div>
              <span class="text-xs text-[color:var(--nav-text-muted)] shrink-0">{{ formatBytes(file.size) }}</span>
              <button type="button" class="shrink-0 px-2 py-1 rounded-lg bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleLearningFolder(file)">移出</button>
            </div>
          </div>
          <div v-else class="rounded-xl border border-dashed border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/30 px-4 py-3 text-xs text-[color:var(--nav-text-muted)]">在下方「搜索文件」列表中勾选资料加入此文件夹。</div>
        </div>
      </section>

      <!-- 搜索文件：搜索栏 + 已上传文件列表 -->
      <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 shadow-[0_8px_30px_rgba(0,0,0,0.08)] p-5 mb-8 lg:flex-1 lg:min-h-0 lg:flex lg:flex-col">
        <div class="flex items-center gap-2 mb-4">
          <span class="flex size-9 items-center justify-center rounded-xl bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--nav-text)]">
            <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
          </span>
          <span class="text-sm font-semibold text-[color:var(--app-text)]">搜索文件</span>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-end gap-3 mb-4">
          <div class="flex-1 min-w-0">
            <label class="block text-xs text-[color:var(--nav-text-muted)] mb-1">文件名或扩展名</label>
            <input v-model="query" type="text" placeholder="输入关键词筛选..." class="w-full rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)] px-4 py-2.5 text-sm text-[color:var(--app-text)] outline-none focus:border-[color:var(--nav-active-border)] focus:ring-2 focus:ring-[color:var(--nav-active-border)]/20 transition-colors" />
          </div>
          <div class="w-full sm:w-40">
            <label class="block text-xs text-[color:var(--nav-text-muted)] mb-1">类型</label>
            <select v-model="typeFilter" class="w-full rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)] px-3 py-2.5 text-sm text-[color:var(--app-text)] outline-none focus:border-[color:var(--nav-active-border)] transition-colors cursor-pointer">
              <option v-for="opt in typeOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
            </select>
          </div>
          <div class="text-xs text-[color:var(--nav-text-muted)] sm:pb-2">共 {{ filteredFiles.length }} 个文件</div>
        </div>

        <div v-if="filteredFiles.length" class="space-y-2 lg:flex-1 lg:min-h-0 lg:overflow-y-auto overflow-x-hidden custom-scroll pr-1">
          <div v-for="file in filteredFiles" :key="file.id" class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/50 hover:bg-[color:var(--app-bg-2)]/80 p-3 flex flex-col sm:flex-row sm:items-center gap-3 transition-colors duration-200">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <div class="size-10 rounded-lg bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] flex items-center justify-center shrink-0">
                <svg viewBox="0 0 24 24" class="size-5 text-[color:var(--nav-text-muted)]" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-sm font-medium text-[color:var(--app-text)] truncate" :title="file.originalName">{{ file.originalName }}</div>
                <div class="flex flex-wrap items-center gap-2 mt-0.5 text-xs text-[color:var(--nav-text-muted)]">
                  <span class="px-1.5 py-0.5 rounded-md bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--nav-text)]">{{ fileKindLabel(file) }}</span>
                  <span v-if="isInLearningFolder(file.id)" class="px-1.5 py-0.5 rounded-md bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--nav-text)]">{{ folderBadgeLabel }}</span>
                  <span>{{ formatBytes(file.size) }}</span>
                  <span>{{ formatDate(file.uploadedAt) }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button type="button" class="p-2 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer inline-flex items-center gap-1.5 text-xs" @click="openPreview(file)" title="预览">
                <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                预览
              </button>
              <button type="button" class="p-2 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer inline-flex items-center gap-1.5 text-xs" @click="toggleLearningFolder(file)" :title="isInLearningFolder(file.id) ? '移出资料' : '加入资料'">
                <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-2.12 0L2.25 15.75m13.5-6.75 2.12-2.12a1.5 1.5 0 0 1 2.12 0L21.75 15.75" /></svg>
                {{ isInLearningFolder(file.id) ? "移出" : "加入" }}
              </button>
              <button type="button" class="p-2 rounded-lg border border-red-500/40 bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20 transition-colors duration-200 cursor-pointer disabled:opacity-60 inline-flex items-center gap-1.5 text-xs" :disabled="busy" title="删除" @click="removeFile(file.id)">
                <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
                删除
              </button>
            </div>
          </div>
        </div>
        <div v-else class="rounded-xl border border-dashed border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/30 py-12 text-center text-sm text-[color:var(--nav-text-muted)] lg:flex-1 lg:min-h-0 lg:flex lg:items-center lg:justify-center">
          还没有上传文件，请在上方「上传文件」区域拖拽或点击选择添加。
        </div>
      </section>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      class="hidden"
      multiple
      accept=".pdf,.ppt,.pptx,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a"
      @change="onFileChange"
    />
  </div>

  <div
    v-if="previewFile"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4"
    @click.self="closePreview"
  >
    <div class="w-full max-w-4xl rounded-3xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-[0_20px_60px_rgba(0,0,0,0.35)] overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-[color:var(--glass-border)]">
        <div class="min-w-0">
          <div class="text-sm text-[color:var(--app-text)] font-semibold truncate" :title="previewFile.originalName">{{ previewFile.originalName }}</div>
          <div class="text-xs text-[color:var(--nav-text-muted)]">{{ fileKindLabel(previewFile) }} · {{ formatBytes(previewFile.size) }}</div>
        </div>
        <div class="flex items-center gap-2">
          <a
            class="px-3 py-1.5 rounded-xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
            :href="previewFile.url"
            target="_blank"
            rel="noreferrer"
          >
            新窗口打开
          </a>
          <button
            type="button"
            class="px-3 py-1.5 rounded-xl bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] text-xs text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
            @click="closePreview"
          >
            关闭
          </button>
        </div>
      </div>
      <div class="p-4 bg-[color:var(--app-bg-2)]/50">
        <div v-if="previewType(previewFile) === 'image'" class="flex justify-center">
          <img :src="previewFile.url" :alt="previewFile.originalName" class="max-h-[70vh] rounded-2xl border border-[color:var(--glass-border)]" />
        </div>
        <div v-else-if="previewType(previewFile) === 'audio'" class="flex justify-center py-8">
          <audio controls :src="previewFile.url" class="w-full"></audio>
        </div>
        <div v-else-if="previewType(previewFile) === 'pdf' || previewType(previewFile) === 'text'" class="h-[70vh]">
          <iframe :src="previewFile.url" class="w-full h-full rounded-2xl border border-[color:var(--glass-border)]" title="文件预览"></iframe>
        </div>
        <div v-else class="text-center text-sm text-stone-400 py-16">该文件类型暂不支持直接预览，请使用“新窗口打开”。</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { deleteFile, listFiles, uploadFiles, type LibraryFile } from "../lib/api";
import { getUserScopedStorageKey, readScopedStorage } from "../lib/userStorage";

const route = useRoute();
const isTeacherPage = computed(() => route.path.startsWith("/teacher/"));

const pageTitle = computed(() => (isTeacherPage.value ? "教师文件库" : "文件库"));
const pageSubtitle = computed(() =>
  isTeacherPage.value ? "集中管理上传的课程资料与教学文档" : "集中管理上传的学习资料与文档"
);
const uploadHint = computed(() =>
  isTeacherPage.value
    ? "上传后可生成教案、测验、试卷、对话等教学资源"
    : "上传后将生成可用于测验、对话、试卷等功能的文件链接"
);
const folderLabel = computed(() => (isTeacherPage.value ? "教学交互文件夹" : "学习交互文件夹"));
const folderHint = computed(() =>
  isTeacherPage.value
    ? "将已上传资料加入此文件夹，可作为教案、测验、对话等功能的课程资料。"
    : "将已上传资料加入此文件夹，可作为测验、对话等功能的学习资料。"
);
const folderBadgeLabel = computed(() => (isTeacherPage.value ? "教学文件夹" : "学习文件夹"));

const files = ref<LibraryFile[]>([]);
const query = ref("");
const typeFilter = ref("all");
const dragActive = ref(false);
const uploading = ref(false);
const busy = ref(false);
const error = ref("");
const fileInputRef = ref<HTMLInputElement | null>(null);
const previewFile = ref<LibraryFile | null>(null);
const learningFolderIds = ref<string[]>([]);
const LEARNING_FOLDER_KEY = computed(() =>
  getUserScopedStorageKey(isTeacherPage.value ? "edumind-learning-folder-teacher" : "edumind-learning-folder")
);

const typeOptions = [
  { key: "all", label: "全部" },
  { key: "pdf", label: "PDF" },
  { key: "doc", label: "DOC" },
  { key: "ppt", label: "PPT" },
  { key: "text", label: "文本" },
  { key: "image", label: "图片" },
  { key: "audio", label: "音频" },
  { key: "video", label: "视频" },
  { key: "other", label: "其他" },
];

const load = async () => {
  error.value = "";
  try {
    const res = await listFiles(isTeacherPage.value ? "teacher" : "student");
    files.value = res.files || [];
    pruneLearningFolder();
  } catch {
    error.value = "文件加载失败，请稍后重试。";
  }
};

const triggerPick = () => fileInputRef.value?.click();

const onFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const list = input.files;
  handleUpload(list);
};

const handleUpload = async (list: FileList | null) => {
  if (!list || uploading.value) return;
  const next = Array.from(list);
  if (!next.length) return;
  uploading.value = true;
  error.value = "";
  try {
    await uploadFiles(next, isTeacherPage.value ? "teacher" : "student");
    await load();
  } catch {
    error.value = "上传失败，请检查文件后重试。";
  } finally {
    uploading.value = false;
    if (fileInputRef.value) fileInputRef.value.value = "";
  }
};

const onDragOver = () => {
  dragActive.value = true;
};

const onDragLeave = () => {
  dragActive.value = false;
};

const onDrop = (e: DragEvent) => {
  dragActive.value = false;
  handleUpload(e.dataTransfer?.files || null);
};

const removeFile = async (id: string) => {
  busy.value = true;
  error.value = "";
  try {
    await deleteFile(id, isTeacherPage.value ? "teacher" : "student");
    await load();
    removeFromLearningFolder(id);
  } catch {
    error.value = "删除失败，请稍后重试。";
  } finally {
    busy.value = false;
  }
};

const openPreview = (file: LibraryFile) => {
  previewFile.value = file;
};

const closePreview = () => {
  previewFile.value = null;
};

const fileKind = (file: LibraryFile) => {
  const name = (file.originalName || "").toLowerCase();
  if (name.endsWith(".pdf")) return "pdf";
  if (name.endsWith(".ppt") || name.endsWith(".pptx")) return "ppt";
  if (name.endsWith(".doc") || name.endsWith(".docx")) return "doc";
  if (name.endsWith(".txt") || name.endsWith(".md")) return "text";

  const mime = file.mimeType || "";
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.startsWith("video/")) return "video";
  return "other";
};

const fileKindLabel = (file: LibraryFile) => {
  const kind = fileKind(file);
  const match = typeOptions.find((opt) => opt.key === kind);
  return match ? match.label : "其他";
};

const previewType = (file: LibraryFile) => {
  const name = (file.originalName || "").toLowerCase();
  const mime = file.mimeType || "";
  if (mime.startsWith("image/") || name.match(/\.(png|jpe?g|webp|gif)$/)) return "image";
  if (mime.startsWith("audio/") || name.match(/\.(mp3|wav|m4a)$/)) return "audio";
  if (name.endsWith(".pdf")) return "pdf";
  if (name.match(/\.(txt|md)$/)) return "text";
  return "other";
};

const formatBytes = (size: number) => {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let idx = 0;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  return `${value.toFixed(value >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
};

const formatDate = (ts: number) => {
  if (!ts) return "-";
  return new Date(ts).toLocaleString();
};

const filteredFiles = computed(() => {
  const q = query.value.trim().toLowerCase();
  const type = typeFilter.value;
  return files.value.filter((file) => {
    const name = (file.originalName || "").toLowerCase();
    const matchesQuery = !q || name.includes(q);
    const matchesType = type === "all" || fileKind(file) === type;
    return matchesQuery && matchesType;
  });
});

const loadLearningFolder = () => {
  try {
    const key = LEARNING_FOLDER_KEY.value;
    const raw = localStorage.getItem(key);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    learningFolderIds.value = Array.isArray(parsed) ? parsed : [];
  } catch {
    learningFolderIds.value = [];
  }
};

const persistLearningFolder = () => {
  localStorage.setItem(LEARNING_FOLDER_KEY.value, JSON.stringify(learningFolderIds.value));
};

const pruneLearningFolder = () => {
  if (!learningFolderIds.value.length) return;
  const existing = new Set(files.value.map((f) => f.id));
  learningFolderIds.value = learningFolderIds.value.filter((id) => existing.has(id));
  persistLearningFolder();
};

const isInLearningFolder = (id: string) => learningFolderIds.value.includes(id);

const removeFromLearningFolder = (id: string) => {
  if (!isInLearningFolder(id)) return;
  learningFolderIds.value = learningFolderIds.value.filter((item) => item !== id);
  persistLearningFolder();
};

const toggleLearningFolder = (file: LibraryFile) => {
  if (isInLearningFolder(file.id)) {
    removeFromLearningFolder(file.id);
    return;
  }
  learningFolderIds.value = [file.id, ...learningFolderIds.value];
  persistLearningFolder();
};

const learningFolderFiles = computed(() => {
  if (!learningFolderIds.value.length) return [] as LibraryFile[];
  const map = new Map(files.value.map((f) => [f.id, f]));
  return learningFolderIds.value.map((id) => map.get(id)).filter(Boolean) as LibraryFile[];
});

const totalCount = computed(() => files.value.length);
const totalSize = computed(() => formatBytes(files.value.reduce((sum, f) => sum + (f.size || 0), 0)));
const latestLabel = computed(() => {
  if (!files.value.length) return "暂无";
  const latest = [...files.value].sort((a, b) => (b.uploadedAt || 0) - (a.uploadedAt || 0))[0];
  return latest ? `${latest.originalName} (${formatDate(latest.uploadedAt)})` : "暂无";
});

onMounted(() => {
  loadLearningFolder();
  load();
});
</script>
