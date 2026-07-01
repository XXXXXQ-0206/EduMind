<template>
  <div class="mt-auto pb-4 pt-4 relative">
    <div class="w-fit flex flex-col items-center mx-auto mb-8 cursor-pointer select-none" @click="toggleOpen">
      <svg
        viewBox="0 0 20 20"
        fill="currentColor"
        class="size-6"
        :style="{ transition: 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }"
      >
        <path
          fill-rule="evenodd"
          d="M9.47 6.47a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 1 1-1.06 1.06L10 8.06l-3.72 3.72a.75.75 0 0 1-1.06-1.06l4.25-4.25Z"
          clip-rule="evenodd"
        />
      </svg>
      <span class="text-sm">{{ busy ? '开始中…' : '探索主题' }}</span>
    </div>

    <div class="w-full max-w-4xl mx-auto overflow-hidden">
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <TopicCard title="数学" @select="startTopic" />
        <TopicCard title="英语" @select="startTopic" />
        <TopicCard title="科学" extra="col-span-1 sm:col-span-2 lg:col-span-1" @select="startTopic" />
      </div>

      <div
        class="overflow-hidden"
        :style="{ transition: 'max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1)', maxHeight: open ? '1000px' : '0px' }"
      >
        <div v-for="(row, i) in moreRows" :key="i" class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <TopicCard
            v-for="(title, j) in row"
            :key="title"
            :title="title"
            :extra="j === 2 ? 'col-span-1 sm:col-span-2 lg:col-span-1' : ''"
            @select="startTopic"
          />
        </div>
      </div>
    </div>

    <div
      class="absolute w-full h-full bottom-0 bg-gradient-to-b from-transparent to-black/80 pointer-events-none"
      :style="{ transition: 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)', opacity: open ? 0 : 1 }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { chatJSON } from "../../lib/api";
import TopicCard from "./TopicCard.vue";

const router = useRouter();
const open = ref(false);
const busy = ref(false);

const moreRows = computed(() => [
  ["历史", "地理", "音乐"],
  ["艺术", "技术", "哲学"],
]);

const toggleOpen = () => {
  open.value = !open.value;
};

const promptFor = (topic: string) => `给我一个清晰的、适合初学者的${topic}课程`;

const startTopic = async (title: string) => {
  if (busy.value) return;
  try {
    busy.value = true;
    const q = promptFor(title);
    const r = await chatJSON({ q });
    router.push({
      path: "/chat",
      query: { chatId: r.chatId, q },
      state: { chatId: r.chatId, q },
    });
  } finally {
    busy.value = false;
  }
};
</script>
