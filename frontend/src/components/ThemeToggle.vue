<template>
  <button
    type="button"
    class="fixed bottom-5 right-5 z-50 inline-flex size-11 items-center justify-center rounded-full border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] text-[color:var(--app-text)] shadow-[0_18px_40px_rgba(2,8,23,0.18)] backdrop-blur transition-colors hover:bg-[color:var(--nav-hover-bg-strong)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring-color)] cursor-pointer"
    @click="theme.toggle"
    :aria-label="theme.mode === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
  >
    <span class="inline-flex size-7 items-center justify-center rounded-full bg-gradient-to-br from-[color:var(--role-pill-from)]/25 to-[color:var(--role-pill-to)]/25">
      <svg v-if="theme.mode === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m0 13.5V21m9-9h-2.25M5.25 12H3m15.364-6.364-1.591 1.591M7.227 16.773l-1.591 1.591m0-12.728 1.591 1.591m11.546 11.546 1.591 1.591" />
        <circle cx="12" cy="12" r="3.5" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79Z" />
      </svg>
    </span>
  </button>
</template>

<script setup lang="ts">
import { useThemeStore } from "../stores/theme";

const theme = useThemeStore();
</script>
