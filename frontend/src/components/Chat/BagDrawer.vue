<template>
  <div v-if="open" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" @click="onClose">
    <div class="absolute right-4 top-4 bottom-4 w-96 bg-stone-950 border border-stone-900 rounded-2xl p-6 overflow-hidden flex flex-col" @click.stop>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-white flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-5 text-sky-300">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V6a4 4 0 0 1 8 0v1" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 7h14l-1.2 12.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8L5 7Z" />
          </svg>
          我的学习包
        </h2>
        <button type="button" @click="onClose" class="p-2 hover:bg-stone-900 rounded-xl transition-colors" aria-label="关闭学习包">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div class="space-y-4">
          <div v-if="items.length === 0" class="text-center text-stone-400 py-8">
            <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-800 bg-stone-900/70">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-6 text-stone-300">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V6a4 4 0 0 1 8 0v1" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 7h14l-1.2 12.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8L5 7Z" />
              </svg>
            </div>
            <p>你的学习包是空的</p>
            <p class="text-sm">添加抽认卡和笔记开始学习吧！</p>
          </div>
          <div v-else>
            <div v-for="item in items" :key="item.id" class="bg-stone-900/60 border border-stone-800 rounded-xl p-3">
              <div class="text-xs uppercase tracking-wide text-stone-400 mb-1">{{ item.kind }}</div>
              <div class="text-white font-medium">{{ item.title }}</div>
              <div class="text-stone-300 text-sm mt-1">{{ item.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4 pt-4 border-t border-stone-900">
        <button type="button" @click="onClear" class="w-full bg-red-900/20 hover:bg-red-900/30 border border-red-800 text-red-400 rounded-xl px-4 py-2 text-sm transition-colors">
          清空所有项目
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
type Item = { id: string; kind: "flashcard" | "note"; title: string; content: string };

const props = defineProps<{
  open: boolean;
  items: Item[];
  onClose: () => void;
  onClear: () => void;
}>();

const onClose = () => props.onClose();
const onClear = () => props.onClear();
</script>
