<template>
  <div class="fixed bottom-4 right-8 z-50">
    <button
      type="button"
      class="relative cursor-pointer hover:scale-105 transition-transform duration-300"
      @click="onClick"
      aria-label="打开学习包"
    >
      <div class="h-16 w-16 rounded-2xl bg-stone-900/80 border border-stone-800 flex items-center justify-center shadow-lg">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-8 text-sky-200">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V6a4 4 0 0 1 8 0v1" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 7h14l-1.2 12.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8L5 7Z" />
        </svg>
      </div>
      <div v-if="count" class="absolute -top-2 -right-2 bg-red-600 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold">
        {{ count }}
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ count: number; onClick: () => void }>();
const onClick = () => props.onClick();
</script>
