<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-shrink-0 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col min-h-0">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-amber-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z" />
          </svg>
        </span>
        {{ folderTitle }}
      </div>
      <div class="text-xs text-[color:var(--nav-text-muted)]">{{ files.length }} 个</div>
    </div>
    <div class="text-xs text-[color:var(--nav-text-muted)] mb-3">{{ folderSubtitle }}</div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="files.length" class="space-y-2 max-h-40 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li
        v-for="file in files"
        :key="file.id"
        class="text-sm text-[color:var(--app-text)] truncate"
        :title="file.originalName"
      >
        {{ file.originalName }}
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">{{ folderEmptyHint }}</div>
  </aside>
</template>

<script setup lang="ts">
import { type Ref, computed, inject, onMounted, ref } from "vue";
import { listFiles, type LibraryFile } from "../lib/api";
import { getUserScopedStorageKey } from "../lib/userStorage";

const learningFolderKeyInjected = inject<Ref<string>>("learningFolderKey");
const chatRoleInjected = inject<Ref<"student" | "teacher">>("chatRole");
const LEARNING_FOLDER_KEY = computed(() => learningFolderKeyInjected?.value ?? getUserScopedStorageKey("pagelm-learning-folder"));

const loading = ref(false);
const folderIds = ref<string[]>([]);
const allFiles = ref<LibraryFile[]>([]);

const loadFolderIds = () => {
  try {
    const key = LEARNING_FOLDER_KEY.value;
    const raw = localStorage.getItem(key);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    folderIds.value = Array.isArray(parsed) ? parsed : [];
  } catch {
    folderIds.value = [];
  }
};

const loadFiles = async () => {
  loading.value = true;
  try {
    const role = chatRoleInjected?.value;
    const res = await listFiles(role);
    allFiles.value = res.files || [];
  } catch {
    allFiles.value = [];
  } finally {
    loading.value = false;
  }
};

const files = computed(() => {
  if (!folderIds.value.length || !allFiles.value.length) return [] as LibraryFile[];
  const map = new Map(allFiles.value.map((f) => [f.id, f]));
  return folderIds.value.map((id) => map.get(id)).filter(Boolean) as LibraryFile[];
});

const isTeacher = computed(() => chatRoleInjected?.value === "teacher");
const folderTitle = computed(() => (isTeacher.value ? "备课资料" : "学习资料"));
const folderSubtitle = computed(() => (isTeacher.value ? "来自教学交互文件夹" : "来自学习交互文件夹"));
const folderEmptyHint = computed(() => (isTeacher.value ? "暂无备课资料，请在文件库添加。" : "暂无学习资料，请在文件库添加。"));

onMounted(async () => {
  loadFolderIds();
  if (folderIds.value.length) {
    await loadFiles();
  }
});
</script>
