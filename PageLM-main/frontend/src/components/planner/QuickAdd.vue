<template>
  <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
    <div class="text-zinc-200 font-medium mb-3 flex items-center gap-2">
      <svg class="size-4 text-sky-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v6m0 0 4-4m-4 4-4-4" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 12h12v7.5A1.5 1.5 0 0 1 16.5 21h-9A1.5 1.5 0 0 1 6 19.5Z" />
      </svg>
      快速添加
    </div>

    <div class="space-y-3">
      <div class="flex gap-2">
        <input
          v-model="text"
          placeholder="例如：数学作业第5章，明天晚上8点截止，大约2小时"
          class="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 placeholder:text-zinc-500 outline-none focus:ring-1 focus:ring-zinc-700"
          @keydown.enter.exact.prevent="handleSubmit"
        />
        <input
          ref="fileInputRef"
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
          class="hidden"
          @change="(e) => handleFileSelect((e.target as HTMLInputElement).files)"
        />
        <button
          type="button"
          class="px-3 py-2 rounded-lg bg-zinc-800 text-zinc-200 border border-zinc-700 hover:bg-zinc-700"
          title="上传作业文件"
          @click="fileInputRef?.click()"
        >
          <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 16V6m0 0-3 3m3-3 3 3" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 16.5V18a2.25 2.25 0 0 0 2.25 2.25h9A2.25 2.25 0 0 0 18.5 18v-1.5" />
          </svg>
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-60 hover:bg-blue-700"
          :disabled="loading || (!text.trim() && selectedFiles.length === 0)"
          @click="handleSubmit"
        >
          {{ loading ? "添加中..." : "添加" }}
        </button>
      </div>

      <div v-if="selectedFiles.length > 0" class="flex flex-wrap gap-2">
        <div v-for="(file, i) in selectedFiles" :key="file.name + i" class="flex items-center gap-1 px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-200">
          <span class="truncate max-w-32" :title="file.name">{{ file.name }}</span>
          <span class="text-zinc-400">({{ Math.round(file.size / 1024) }}KB)</span>
          <button type="button" class="text-zinc-400 hover:text-zinc-200 ml-1" @click="removeFile(i)">×</button>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <div class="text-zinc-400 text-xs">快速模板：</div>
        <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700" @click="text = 'Math homework due tomorrow 8pm ~1.5h'">
          数学作业
        </button>
        <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700" @click="text = 'Read chapter for English class due Friday ~30m'">
          阅读
        </button>
        <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700" @click="text = 'Study for quiz next week ~2h'">
          复习
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

type AddPayload = { text?: string; files?: File[] };

const props = defineProps<{
  onAdd: (data: AddPayload) => Promise<void>;
  loading: boolean;
}>();

const text = ref("");
const selectedFiles = ref<File[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);

const handleFileSelect = (files: FileList | null) => {
  if (!files) return;
  const newFiles = Array.from(files).filter(
    (f) => f.size <= 10 * 1024 * 1024 && (f.type.includes("pdf") || f.type.includes("image") || f.type.includes("text") || f.type.includes("document"))
  );
  selectedFiles.value = [...selectedFiles.value, ...newFiles];
};

const removeFile = (index: number) => {
  selectedFiles.value = selectedFiles.value.filter((_, i) => i !== index);
};

const handleSubmit = async () => {
  if (!text.value.trim() && selectedFiles.value.length === 0) return;
  await props.onAdd({ text: text.value, files: selectedFiles.value });
  text.value = "";
  selectedFiles.value = [];
};
</script>
