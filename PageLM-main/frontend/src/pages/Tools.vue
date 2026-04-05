<template>
  <div class="min-h-screen w-full px-4 lg:pl-28 lg:pr-4">
    <div class="max-w-6xl mx-auto pt-6 px-4 pb-14">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <RouterLink
            to="/"
            class="p-2 rounded-xl bg-stone-950 border border-zinc-800 hover:bg-stone-900 transition-colors"
            aria-label="Back"
          >
            <svg viewBox="0 0 24 24" class="size-5 text-stone-300" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
            </svg>
          </RouterLink>
          <h1 class="text-2xl font-semibold text-white flex items-center gap-3">学习工具</h1>
        </div>
        <div class="px-3 py-1 rounded-full bg-gradient-to-r from-sky-500/20 to-blue-500/20 border border-sky-500/30 text-sky-300 text-xs font-medium">
          BETA
        </div>
      </div>

      <div class="grid gap-6 mb-12">
        <SmartNotes />
        <PodcastGenerator />
        <Transcriber />
        <ComingSoon />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import SmartNotes from "../components/Tools/SmartNotes.vue";
import PodcastGenerator from "../components/Tools/PodcastGenerator.vue";
import Transcriber from "../components/Tools/Transcriber.vue";
import ComingSoon from "../components/Tools/ComingSoon.vue";
</script>
