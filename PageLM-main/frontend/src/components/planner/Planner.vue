<template>
  <div class="rounded-2xl border border-zinc-800 bg-stone-950">
    <div class="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
      <div class="text-stone-200 font-medium">作业规划器</div>
      <div class="flex items-center gap-2">
        <div class="text-xs bg-zinc-900 border border-zinc-800 rounded overflow-hidden">
          <button type="button" class="px-2 py-1" :class="view === 'today' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-300'" @click="view = 'today'">今日</button>
          <button type="button" class="px-2 py-1" :class="view === 'list' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-300'" @click="view = 'list'">列表</button>
          <button type="button" class="px-2 py-1" :class="view === 'mindmap' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-300'" @click="view = 'mindmap'">思维导图</button>
        </div>
        <button type="button" class="text-xs px-2 py-1 rounded bg-stone-800 text-stone-200" @click="reload">刷新</button>
      </div>
    </div>

    <div class="p-4 space-y-6">
      <div v-if="notifications.length > 0" class="space-y-2">
        <div
          v-for="n in notifications"
          :key="n.id"
          :class="[
            'px-3 py-2 rounded-lg text-sm',
            n.type === 'error'
              ? 'bg-red-900/50 border border-red-800 text-red-200'
              : n.type === 'success'
                ? 'bg-green-900/50 border border-green-800 text-green-200'
                : n.type === 'reminder'
                  ? 'bg-yellow-900/50 border border-yellow-800 text-yellow-200'
                  : n.type === 'break'
                    ? 'bg-purple-900/50 border border-purple-800 text-purple-200'
                    : 'bg-blue-900/50 border border-blue-800 text-blue-200'
          ]"
        >
          {{ n.message }}
        </div>
      </div>

      <div v-if="view === 'today'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <TodayFocus :tasks="tasks" :onStartSession="startNow" :onCompleteTask="(id) => mark(id, 'done')" />
        </div>
        <div>
          <QuickAdd :onAdd="add" :loading="loading" />
        </div>
      </div>

      <div v-else-if="view === 'mindmap'" class="rounded-xl border border-zinc-800 overflow-hidden h-[75vh]">
        <PlannerMindmap
          :tasks="tasks"
          :plan="plan"
          :onPlan="planTask"
          :onAssist="gen"
          :onUpdateStatus="mark"
          :onUpload="onUpload"
          :onDelete="del"
          :onStartNow="startNow"
          :onUpdateNotes="updateNotes"
        />
      </div>

      <div v-else class="grid gap-3">
        <div v-for="t in tasks" :key="t.id" class="rounded-xl border border-zinc-800 bg-stone-950 p-3">
          <div class="flex items-center justify-between">
            <div class="min-w-0">
              <div class="text-zinc-100 font-medium truncate">{{ t.title }}</div>
              <div class="text-zinc-400 text-xs">
                截止 {{ fmtTime(t.dueAt) }} · {{ t.estMins }} 分钟 · P{{ t.priority }}
                <span v-if="t.files && t.files.length > 0"> · {{ t.files.length }} 个文件</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <select :value="t.status" class="bg-stone-900 border border-zinc-800 text-stone-200 text-xs rounded px-2 py-1" @change="(e) => handleStatusChange(t.id, e)">
                <option value="todo">待办</option>
                <option value="doing">进行中</option>
                <option value="done">已完成</option>
                <option value="blocked">已阻塞</option>
              </select>
              <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-200" @click="planTask(t.id)">计划</button>
              <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-200" @click="gen(t.id, 'summary')">摘要</button>
              <button type="button" class="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-200" @click="gen(t.id, 'flashcards')">闪卡</button>
              <button type="button" class="text-xs px-2 py-1 rounded bg-red-600 text-white" @click="del(t.id)">删除</button>
            </div>
          </div>

          <div v-if="t.files && t.files.length > 0" class="mt-3 border-t border-zinc-800 pt-3">
            <div class="text-zinc-300 text-xs mb-2">附件文件：</div>
            <div class="flex flex-wrap gap-2">
              <div v-for="file in t.files" :key="file.id" class="flex items-center gap-1 px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-200">
                <span class="truncate max-w-32" :title="file.originalName">{{ file.originalName }}</span>
                <span class="text-zinc-400">({{ Math.round(file.size / 1024) }}KB)</span>
                <button type="button" class="text-zinc-400 hover:text-red-400 ml-1" title="Delete file" @click="deleteFile(t.id, file.id)">×</button>
              </div>
            </div>
          </div>

          <div v-if="materials[t.id]?.summary" class="mt-3 text-sm text-zinc-200 whitespace-pre-wrap">
            {{ materials[t.id].summary.answer || materials[t.id].summary }}
          </div>
          <div v-if="Array.isArray(materials[t.id]?.flashcards?.flashcards)" class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div v-for="(c, i) in materials[t.id].flashcards.flashcards" :key="i" class="border border-zinc-800 rounded-lg p-2">
              <div class="text-zinc-200 text-sm font-medium">Q: {{ c.q }}</div>
              <div class="text-zinc-400 text-sm">A: {{ c.a }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="view === 'list'">
        <div class="text-stone-300 text-sm mb-2">周计划</div>
        <div v-if="plan" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <DaySlots v-for="d in plan.days" :key="d.date" :date="d.date" :slots="d.slots" :tasks="taskIndex" />
        </div>
        <div v-else class="text-stone-500 text-sm">暂无计划</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, onBeforeUnmount, onMounted, ref } from "vue";
import PlannerMindmap from "./PlannerMindmap.vue";
import TodayFocus from "./TodayFocus.vue";
import QuickAdd from "./QuickAdd.vue";
import {
  connectPlannerStream,
  plannerDelete,
  plannerIngest,
  plannerList,
  plannerMaterials,
  plannerPlan,
  plannerUpdate,
  plannerWeekly,
  plannerCreateWithFiles,
  plannerUploadFiles,
  plannerDeleteFile,
  type PlannerEvent,
  type PlannerSlot,
  type PlannerTask,
  type WeeklyPlan,
} from "../../lib/api";

const fmtTime = (ts: number) => {
  const d = new Date(ts);
  return d.toLocaleString(undefined, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
};

const DaySlots = defineComponent({
  props: {
    date: { type: String, required: true },
    slots: { type: Array as () => PlannerSlot[], required: true },
    tasks: { type: Object as () => Record<string, PlannerTask>, required: true },
  },
  setup(props) {
    const fmt = (ts: number) => {
      const d = new Date(ts);
      return d.toLocaleString(undefined, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
    };
    return { fmt };
  },
  template: `
    <div class="rounded-xl border border-zinc-800 bg-stone-950 p-3">
      <div class="text-xs text-stone-400 mb-2">{{ date }}</div>
      <div class="space-y-2">
        <div v-if="slots.length === 0" class="text-stone-500 text-sm">No slots</div>
        <div v-for="s in slots" :key="s.id" class="flex items-center justify-between text-sm text-stone-200/90">
          <div class="truncate">
            <span class="px-1.5 py-0.5 rounded bg-stone-800/60 text-[10px] mr-2">{{ s.kind }}</span>
            <span class="font-medium">{{ tasks[s.taskId]?.title || s.taskId }}</span>
          </div>
          <div class="text-stone-400 text-xs">{{ fmt(s.start) }} → {{ new Date(s.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</div>
        </div>
      </div>
    </div>
  `,
});

const view = ref<"today" | "list" | "mindmap">("today");
const loading = ref(false);
const tasks = ref<PlannerTask[]>([]);
const plan = ref<WeeklyPlan | null>(null);
const materials = ref<Record<string, any>>({});
const loadingStates = ref<Record<string, { plan?: boolean; summary?: boolean; flashcards?: boolean }>>({});
const notifications = ref<Array<{ id: string; type: string; message: string; at: number }>>([]);
const sid = Math.random().toString(36).slice(2, 10);
const wsRef = ref<ReturnType<typeof connectPlannerStream> | null>(null);

const taskIndex = computed(() => Object.fromEntries(tasks.value.map((t) => [t.id, t])));

const slotsByTask = computed(() => {
  const m: Record<string, PlannerSlot[]> = {};
  for (const d of plan.value?.days || []) {
    for (const s of d.slots) (m[s.taskId] ||= []).push(s);
  }
  for (const k of Object.keys(m)) m[k].sort((a, b) => a.start - b.start);
  return m;
});

const addNotification = (type: string, message: string) => {
  const id = Math.random().toString(36).slice(2);
  notifications.value = [{ id, type, message, at: Date.now() }, ...notifications.value.slice(0, 4)];
  setTimeout(() => {
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }, 5000);
};

const reload = async () => {
  const res = await plannerList();
  tasks.value = res.tasks;
  const wp = await plannerWeekly(false);
  plan.value = wp.plan;
};

const add = async (data?: { text?: string; files?: File[] }) => {
  const taskText = data?.text || "";
  const taskFiles = data?.files || [];
  if (!taskText.trim() && taskFiles.length === 0) return;
  loading.value = true;
  try {
    if (taskFiles.length > 0) {
      const { task } = await plannerCreateWithFiles({ text: taskText, files: taskFiles });
      tasks.value = [task, ...tasks.value.filter((x) => x.id !== task.id)];
    } else {
      const { task } = await plannerIngest(taskText);
      tasks.value = [task, ...tasks.value.filter((x) => x.id !== task.id)];
    }
  } finally {
    loading.value = false;
  }
};

const planTask = async (id: string) => {
  loadingStates.value = { ...loadingStates.value, [id]: { ...loadingStates.value[id], plan: true } };
  try {
    const result = await plannerPlan(id, false);
    const { task } = result;
    tasks.value = tasks.value.map((x) => (x.id === id ? (task as any) : x));
    const wp = await plannerWeekly(false);
    plan.value = wp.plan;
    addNotification("success", "任务计划已制定");
  } catch (error: any) {
    addNotification("error", `制定任务计划失败：${error?.message || '未知错误'}`);
  } finally {
    loadingStates.value = { ...loadingStates.value, [id]: { ...loadingStates.value[id], plan: false } };
  }
};

const gen = async (id: string, kind: "summary" | "studyGuide" | "flashcards" | "quiz") => {
  loadingStates.value = { ...loadingStates.value, [id]: { ...loadingStates.value[id], [kind]: true } };
  try {
    const { data } = await plannerMaterials(id, kind);
    materials.value = { ...materials.value, [id]: { ...(materials.value[id] || {}), [kind]: data } };
  } finally {
    loadingStates.value = { ...loadingStates.value, [id]: { ...loadingStates.value[id], [kind]: false } };
  }
};

const onUpload = async (id: string, file: File) => {
  try {
    await plannerUploadFiles(id, [file]);
  } catch {
    addNotification("error", "文件上传失败");
  }
};

const deleteFile = async (taskId: string, fileId: string) => {
  try {
    await plannerDeleteFile(taskId, fileId);
  } catch {
    addNotification("error", "文件删除失败");
  }
};

const del = async (id: string) => {
  await plannerDelete(id);
  tasks.value = tasks.value.filter((x) => x.id !== id);
};

const mark = async (id: string, status: PlannerTask["status"]) => {
  const { task } = await plannerUpdate(id, { status });
  tasks.value = tasks.value.map((x) => (x.id === id ? task : x));
};

const startNow = async (id: string) => {
  await mark(id, "doing");
  if (!slotsByTask.value[id]?.length) await planTask(id);
};

const updateNotes = async (id: string, notes: string) => {
  const { task } = await plannerUpdate(id, { notes });
  tasks.value = tasks.value.map((x) => (x.id === id ? task : x));
};

const handleStatusChange = (id: string, e: Event) => {
  const value = (e.target as HTMLSelectElement).value as PlannerTask["status"];
  mark(id, value);
};

onMounted(async () => {
  wsRef.value = connectPlannerStream(sid, (ev: PlannerEvent) => {
    if (ev.type === "plan.update") {
      tasks.value = tasks.value.map((x) => (x.id === ev.taskId ? ({ ...x, plan: { ...(x as any).plan, slots: ev.slots } } as any) : x));
      plannerWeekly(false).then((wp) => (plan.value = wp.plan)).catch(() => undefined);
    }
    if (ev.type === "task.created") {
      tasks.value = [ev.task, ...tasks.value.filter((x) => x.id !== ev.task.id)];
      addNotification("success", `任务 "${ev.task.title}" 已创建`);
    }
    if (ev.type === "task.updated") {
      tasks.value = tasks.value.map((x) => (x.id === ev.task.id ? ev.task : x));
    }
    if (ev.type === "task.deleted") {
      tasks.value = tasks.value.filter((x) => x.id !== ev.taskId);
      addNotification("info", "任务已删除");
    }
    if (ev.type === "task.files.added") {
      tasks.value = tasks.value.map((x) =>
        x.id === ev.taskId ? { ...x, files: [...(x.files || []), ...ev.files] } : x
      );
      addNotification("success", `${ev.files.length} 个文件已上传`);
    }
    if (ev.type === "task.file.removed") {
      tasks.value = tasks.value.map((x) =>
        x.id === ev.taskId ? { ...x, files: (x.files || []).filter((f) => f.id !== ev.fileId) } : x
      );
    }
    if (ev.type === "daily.digest") addNotification("info", ev.message);
    if (ev.type === "reminder") {
      addNotification("reminder", ev.text);
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("作业提醒", { body: ev.text });
      }
    }
    if (ev.type === "break.reminder") addNotification("break", ev.text);
    if (ev.type === "evening.review") addNotification("info", ev.message);
    if (ev.type === "session.started") addNotification("success", "学习会话已开始");
    if (ev.type === "session.ended") addNotification("success", `会话已完成：${ev.session.minutesWorked} 分钟`);
    if (ev.type === "materials.chunk") materials.value = { ...materials.value, _chunks: [...(materials.value._chunks || []), ev] };
  });

  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }

  await reload();
});

onBeforeUnmount(() => {
  try {
    wsRef.value?.close();
  } catch {
    return;
  }
});
</script>
