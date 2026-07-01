<template>
  <div class="flex flex-col min-h-screen w-full px-4 lg:pl-28 lg:pr-4">
    <div class="w-full max-w-4xl mx-auto p-4 pt-10 pb-24">
      <div class="rounded-3xl border border-slate-200/10 bg-slate-900/40 p-8 shadow-[0_12px_40px_rgba(0,0,0,0.35)]">
        <h1 class="text-2xl font-semibold text-white mb-2">{{ title }}</h1>
        <p class="text-slate-300">该页面正在迁移到 Vue 3。下一阶段会恢复完整功能。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string }>();
</script>
