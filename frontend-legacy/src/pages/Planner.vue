<template>
  <div class="min-h-screen w-full lg:pl-28">
    <main class="py-2">
      <div class="mx-auto max-w-6xl">
        <header class="flex items-center justify-between pt-4 z-10 relative mb-6">
          <div class="flex items-center gap-3">
            <RouterLink
              to="/"
              class="p-2 rounded-xl bg-stone-950 border border-stone-900 hover:bg-stone-900 transition-colors"
              aria-label="Back"
            >
              <svg viewBox="0 0 24 24" class="size-5 text-stone-300" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
              </svg>
            </RouterLink>
            <h1 class="text-2xl font-semibold text-white flex items-center gap-3">作业规划器</h1>
            <span class="px-2 py-0.5 rounded-full bg-gradient-to-r from-sky-500/20 to-blue-500/20 border border-sky-500/30 text-sky-300 text-[10px] font-medium">BETA</span>
          </div>
        </header>
        <Planner />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import Planner from "../components/planner/Planner.vue";
</script>
