<template>
  <div class="group rounded-2xl bg-stone-950 border border-zinc-800 p-4 hover:border-sky-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-sky-500/10">
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <div class="text-xs uppercase tracking-wide text-sky-400 font-semibold">笔记生成器</div>
          <div class="w-2 h-2 rounded-full bg-gradient-to-r from-sky-400 to-cyan-400 animate-pulse"></div>
        </div>
        <div class="text-white font-semibold text-xl mb-2">智能笔记</div>
        <div class="text-stone-300 text-sm leading-relaxed">
          将任何主题转化为全面、结构化的学习笔记。非常适合备考和研究。
        </div>
      </div>
    </div>

    <div class="mt-6 space-y-3">
      <div class="flex gap-2">
        <div class="relative flex-1">
          <input
            v-model="topic"
            placeholder="输入您的主题..."
            class="w-full px-4 py-3 pr-16 rounded-xl bg-stone-900/70 border border-zinc-700 text-white placeholder-zinc-400 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 outline-none transition-all duration-300"
            @keydown.enter.exact.prevent="onGenerate"
          />
        </div>
        <button
          type="button"
          @click="onGenerate"
          :disabled="busy || !topic.trim()"
          class="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-500 hover:from-sky-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-all duration-300"
        >
          {{ busy ? "生成中…" : "生成" }}
        </button>
      </div>

      <div v-if="status" class="p-4 rounded-xl bg-sky-950/40 border border-sky-800/40 text-sky-200 font-medium">
        {{ status }}
      </div>

      <a
        v-if="filePath"
        :href="filePath"
        target="_blank"
        rel="noopener noreferrer"
        class="block p-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-medium text-center"
      >
        下载笔记
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { smartnotesStart, connectSmartnotesStream, type SmartNotesEvent } from "../../lib/api";

const topic = ref("");
const busy = ref(false);
const status = ref("");
const filePath = ref<string | null>(null);

const onGenerate = async () => {
  if (!topic.value.trim() || busy.value) return;
  busy.value = true;
  status.value = "正在启动…";
  filePath.value = null;

  try {
    const { noteId } = await smartnotesStart({ topic: topic.value });
    const { close } = connectSmartnotesStream(noteId, (ev: SmartNotesEvent) => {
      if (ev.type === "phase") status.value = `状态: ${ev.value}`;
      if (ev.type === "file") {
        filePath.value = ev.file;
        status.value = "就绪";
      }
      if (ev.type === "done") {
        status.value = "完成";
        close();
        busy.value = false;
      }
      if (ev.type === "error") {
        status.value = `错误: ${ev.error}`;
        close();
        busy.value = false;
      }
    });
  } catch (e: any) {
    status.value = e?.message || "失败";
    busy.value = false;
  }
};
</script>
