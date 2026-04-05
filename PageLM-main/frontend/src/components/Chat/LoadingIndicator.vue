<template>
  <div class="w-full max-w-4xl rounded-2xl p-6 border border-stone-900 bg-stone-950">
    <div class="flex items-center gap-4">
      <div class="relative h-5 w-5">
        <span class="absolute inset-0 rounded-full border-2 border-stone-700 animate-ping" />
        <span class="absolute inset-0 rounded-full border-2 border-stone-500" />
      </div>
      <div class="text-stone-300">{{ label }}</div>
    </div>

    <div class="mt-4 space-y-2">
      <div class="h-3 rounded bg-stone-800/60 animate-pulse" />
      <div class="h-3 w-5/6 rounded bg-stone-800/60 animate-pulse" />
      <div class="h-3 w-2/3 rounded bg-stone-800/60 animate-pulse" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ label?: string }>(), {
  label: "正在准备你的回答…",
});
</script>
