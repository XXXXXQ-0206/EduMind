<template>
  <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
    <div class="text-zinc-200 font-medium mb-4 flex items-center gap-2">
      <svg class="size-4 text-sky-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m13.5-4.5-2.12 2.12M7.62 16.38 5.5 18.5m0-13 2.12 2.12M16.38 16.38 18.5 18.5" />
      </svg>
      今日焦点
    </div>

    <div class="space-y-4">
      <div v-if="activeTasks.length > 0">
        <div class="text-zinc-300 text-sm mb-2">正在处理：</div>
        <div class="space-y-2">
          <div v-for="task in activeTasks" :key="task.id" class="bg-blue-900/30 border border-blue-800 rounded-lg p-3">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-blue-200 font-medium">{{ task.title }}</div>
                <div class="text-blue-300 text-xs">
                  {{ task.course }} • {{ task.estMins }} 分钟 • 截止 {{ fmtTime(task.dueAt) }}
                </div>
              </div>
              <button type="button" class="px-3 py-1 rounded bg-green-600 text-white text-xs hover:bg-green-700" @click="onCompleteTask(task.id)">
                完成
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="todayTasks.length > 0">
        <div class="text-zinc-300 text-sm mb-2">今日截止 ({{ todayTasks.length }}):</div>
        <div class="space-y-2">
          <div v-for="task in todayTasks.slice(0, 3)" :key="task.id" class="bg-zinc-900 border border-zinc-800 rounded-lg p-3">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-zinc-200 font-medium">{{ task.title }}</div>
                <div class="text-zinc-400 text-xs">{{ task.course }} • {{ task.estMins }} 分钟 • P{{ task.priority }}</div>
              </div>
              <button type="button" class="px-3 py-1 rounded bg-blue-600 text-white text-xs hover:bg-blue-700" @click="onStartSession(task.id)">
                开始
              </button>
            </div>
          </div>
          <div v-if="todayTasks.length > 3" class="text-zinc-400 text-xs text-center">
            +{{ todayTasks.length - 3 }} 个今日截止的任务
          </div>
        </div>
      </div>

      <div v-if="urgentTasks.length > 0">
        <div class="text-zinc-300 text-sm mb-2">紧急任务（24小时内）：</div>
        <div class="space-y-2">
          <div v-for="task in urgentTasks" :key="task.id" class="bg-yellow-900/20 border border-yellow-800 rounded-lg p-3">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-yellow-200 font-medium">{{ task.title }}</div>
                <div class="text-yellow-300 text-xs">
                  {{ task.course }} • 剩余 {{ Math.round(Math.max(0, (task.dueAt - Date.now()) / (1000 * 60 * 60))) }} 小时 • {{ task.estMins }} 分钟
                </div>
              </div>
              <button type="button" class="px-3 py-1 rounded bg-yellow-600 text-white text-xs hover:bg-yellow-700" @click="onStartSession(task.id)">
                开始
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="todayTasks.length === 0 && urgentTasks.length === 0 && activeTasks.length === 0" class="text-center py-8 text-zinc-400">
        <div class="mx-auto size-10 rounded-full bg-zinc-900 flex items-center justify-center mb-2">
          <svg class="size-5 text-zinc-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>
        <div class="text-sm">今天没有紧急任务！</div>
        <div class="text-xs text-zinc-500">很好地掌握了你的工作进度。</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PlannerTask } from "../../lib/api";

const props = defineProps<{
  tasks: PlannerTask[];
  onStartSession: (taskId: string) => void;
  onCompleteTask: (taskId: string) => void;
}>();

const today = new Date().toISOString().slice(0, 10);

const todayTasks = computed(() =>
  props.tasks.filter((t) => new Date(t.dueAt).toISOString().slice(0, 10) === today && t.status !== "done")
);

const urgentTasks = computed(() =>
  props.tasks
    .filter((t) => {
      const hoursUntilDue = (t.dueAt - Date.now()) / (1000 * 60 * 60);
      return hoursUntilDue < 24 && hoursUntilDue > 0 && t.status !== "done";
    })
    .slice(0, 3)
);

const activeTasks = computed(() => props.tasks.filter((t) => t.status === "doing"));

const fmtTime = (ts: number) => new Date(ts).toLocaleString(undefined, { hour: "2-digit", minute: "2-digit" });
</script>
