<template>
  <button
    type="button"
    :class="['w-full h-48 relative rounded-3xl border border-stone-900 bg-stone-950 hover:scale-105 transition-transform duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-stone-700 disabled:opacity-60', extra]"
    :title="title"
    @click="$emit('select', title)"
  >
    <img :src="imgSrc" :alt="title" class="w-full h-full rounded-3xl object-cover" draggable="false" />
    <div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-transparent to-black" />
    <div class="absolute right-0 bottom-0 pr-4 pb-4 text-stone-200 text-xl sm:text-2xl">{{ title }}</div>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ title: string; extra?: string }>();

defineEmits<{ select: [title: string] }>();

const imgSrc = computed(() => `/pictures/${encodeURIComponent(props.title.toLowerCase())}.png`);
</script>
