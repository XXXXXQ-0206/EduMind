<template>
  <div class="hidden lg:block">
    <div class="sticky top-6 h-[calc(100vh-8rem)] flex flex-col">
      <div class="mb-5">
        <div class="rounded-2xl bg-stone-950/80 border border-zinc-900 px-4 py-3 flex items-center justify-between">
          <h3 class="text-stone-100 font-semibold tracking-wide">重要主题</h3>
          <span class="text-xs text-stone-400">{{ items.length }}</span>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto pr-1 custom-scroll space-y-4 mb-8">
        <div v-if="items.length === 0" class="text-stone-400 text-sm bg-stone-950/60 border border-zinc-900 rounded-2xl p-6 text-center">
          暂无闪卡
        </div>
        <div v-else>
          <div
            v-for="(card, i) in items"
            :key="`${i}-${card.q}`"
            class="group rounded-2xl bg-stone-950/80 border border-zinc-900 hover:bg-stone-900/80 transition-colors shadow-[0_6px_24px_rgba(0,0,0,0.35)]"
          >
            <div class="p-5">
              <div class="flex items-start gap-3">
                <div class="flex-1 min-w-0">
                  <h4 class="text-stone-50 text-sm font-medium leading-5 truncate">{{ card.q }}</h4>
                  <p class="text-stone-400 text-xs leading-5 mt-1 line-clamp-3">{{ card.a }}</p>
                </div>
                <button
                  type="button"
                  @click="onAdd({ kind: 'flashcard', title: card.q, content: card.a })"
                  class="shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-xl bg-stone-900/70 border border-zinc-800 text-stone-400 hover:text-white hover:bg-stone-800 transition-colors"
                  aria-label="添加到收藏"
                  title="添加到收藏"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M19 12H5" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FlashCard } from "../../lib/api";

defineProps<{
  items: FlashCard[];
  onAdd: (item: { kind: "flashcard" | "note"; title: string; content: string }) => void;
}>();
</script>
