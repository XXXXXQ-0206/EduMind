<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v10.5H5.25z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75v-1.5h7.5v1.5" />
          </svg>
        </span>
        历史笔记
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5"
        @click="startNewNote"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建笔记
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="notes.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="note in notes" :key="note.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
            @click="openNote(note.id)"
            @contextmenu.prevent="openContextMenu($event, note)"
            :title="note.title || '未命名笔记'"
          >
            <div class="truncate">{{ note.title || "未命名笔记" }}</div>
            <div class="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-[color:var(--nav-text-muted)]">
              <span>{{ formatTime(note.at) }}</span>
              <span>·</span>
              <span>{{ lengthLabel(note.length) }}</span>
              <span
                class="rounded-full border px-1.5 py-0.5 font-semibold"
                :class="noteStatusTone(note)"
              >
                {{ noteStatusLabel(note) }}
              </span>
            </div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="toggleDetails(note.id)"
            aria-label="查看笔记详情"
            :title="'查看笔记详情'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-sky-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
            @click.stop="removeNote(note.id)"
            aria-label="删除笔记"
            :title="'删除笔记'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
        <div v-if="expandedId === note.id" class="mt-3 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-3 space-y-3 max-h-64 overflow-y-auto custom-scroll">
          <div v-if="details[note.id]" class="space-y-2">
            <div class="text-xs text-[color:var(--nav-text-muted)]">摘要</div>
            <div class="text-xs text-[color:var(--app-text)] whitespace-pre-wrap">{{ details[note.id].summary || '暂无摘要' }}</div>
            <div v-if="details[note.id].questions?.length" class="pt-2">
              <div class="text-xs text-[color:var(--nav-text-muted)]">要点问题</div>
              <ul class="mt-2 space-y-1">
                <li v-for="(q, i) in details[note.id].questions" :key="i" class="text-xs text-[color:var(--app-text)]">
                  <div>Q{{ i + 1 }}：{{ q }}</div>
                  <div v-if="details[note.id].answers?.[i]" class="text-[color:var(--nav-text-muted)]">A：{{ details[note.id].answers?.[i] }}</div>
                </li>
              </ul>
            </div>
            <a
              v-if="notesFile(note.id)"
              :href="notesFile(note.id)"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 text-xs text-emerald-300 hover:text-emerald-200"
            >
              <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
              </svg>
              下载 PDF
            </a>
          </div>
          <div v-else-if="note.status === 'error'" class="text-xs text-rose-300">
            {{ friendlyNoteMessage(note.error) }}
          </div>
          <div v-else-if="note.status === 'pending' || note.status === 'generating'" class="text-xs text-[color:var(--nav-text-muted)]">
            当前笔记仍在生成中，点击条目会进入等待页并持续拉取结果。
          </div>
          <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无笔记详情</div>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史笔记</div>
    <HistoryContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="closeContextMenu"
      @select="addNoteToBag"
    />
  </aside>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deleteSmartNote, friendlyTaskMessage, getSmartNoteDetail, listSmartNotes, type SmartNoteMeta, type SmartNotesPayload } from "../../lib/api";
import { env } from "../../config/env";
import { getAuthToken } from "../../lib/auth";
import { addLearningBagRecord } from "../../lib/learningBag";
import HistoryContextMenu from "../common/HistoryContextMenu.vue";

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const notes = ref<SmartNoteMeta[]>([]);
const expandedId = ref<string | null>(null);
const details = ref<Record<string, SmartNotesPayload>>({});
const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextTarget = ref<{ id: string; title?: string; at?: number } | null>(null);

const loadNotes = async () => {
  loading.value = true;
  try {
    const res = await listSmartNotes();
    notes.value = Array.isArray(res?.notes) ? res.notes : [];
  } catch {
    notes.value = [];
  } finally {
    loading.value = false;
  }
};

const openNote = (id: string) => {
  if (!id) return;
  const currentId = route.query.noteId as string;
  if (currentId === id) {
    router.replace({ path: "/smart-notes" }).then(() => {
      router.push({ path: "/smart-notes", query: { noteId: id, t: String(Date.now()) }, state: { noteId: id } });
    });
    return;
  }
  router.push({ path: "/smart-notes", query: { noteId: id, t: String(Date.now()) }, state: { noteId: id } });
};

const openContextMenu = (event: MouseEvent, note: { id: string; title?: string; at?: number }) => {
  contextTarget.value = note;
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

const addNoteToBag = () => {
  const note = contextTarget.value;
  if (!note?.id) return;
  addLearningBagRecord({
    type: "note",
    refId: note.id,
    title: note.title || "未命名笔记",
    subtitle: formatTime(note.at),
    path: "/smart-notes",
    query: { noteId: note.id },
  });
};

const startNewNote = () => {
  router.push({ path: "/smart-notes", query: { new: String(Date.now()) } });
};

const toggleDetails = async (id: string) => {
  if (!id) return;
  if (expandedId.value === id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = id;
  if (!details.value[id]) {
    try {
      const res = await getSmartNoteDetail(id);
      if (res?.ok && res.notes) {
        details.value = { ...details.value, [id]: res.notes };
      }
    } catch {
      return;
    }
  }
};

const resolveNoteFileUrl = (raw?: string | null) => {
  if (!raw) return "";
  const value = String(raw).trim();
  if (!value) return "";
  try {
    const backend = new URL(env.backend);
    const parsed = new URL(value, env.backend);
    const isNoteAsset =
      parsed.pathname.includes("/storage/smartnotes/") ||
      parsed.pathname.includes("/smartnotes/");
    if (isNoteAsset && parsed.origin !== backend.origin) {
      parsed.protocol = backend.protocol;
      parsed.host = backend.host;
    }
    if (parsed.pathname.includes("/smartnotes/") && !parsed.pathname.includes("/storage/smartnotes/")) {
      const token = getAuthToken();
      if (token) parsed.searchParams.set("token", token);
    }
    return parsed.toString();
  } catch {
    return value;
  }
};

const notesFile = (id: string) => {
  const hit = notes.value.find((item) => item.id === id);
  return resolveNoteFileUrl(hit?.file || "");
};

const removeNote = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该笔记吗？");
  if (!ok) return;
  const prev = notes.value;
  notes.value = prev.filter((item) => item.id !== id);
  try {
    await deleteSmartNote(id);
    if ((route.query.noteId as string) === id) {
      router.push({ path: "/smart-notes" });
    }
    await loadNotes();
  } catch {
    notes.value = prev;
  }
};

const lengthLabel = (value?: string) => {
  if (value === "rough") return "粗略";
  if (value === "detailed") return "详细";
  return "中等";
};

const noteStatusLabel = (note: SmartNoteMeta) => {
  if (note.status === "ready") return "已完成";
  if (note.status === "error") return "失败";
  return "生成中";
};

const noteStatusTone = (note: SmartNoteMeta) => {
  if (note.status === "ready") return "border-emerald-300/50 bg-emerald-100/70 text-emerald-700";
  if (note.status === "error") return "border-rose-300/50 bg-rose-100/70 text-rose-700";
  return "border-amber-300/50 bg-amber-100/70 text-amber-800";
};

const friendlyNoteMessage = (value?: string) =>
  friendlyTaskMessage(value, {
    feature: "smartnotes",
    fallback: "这份笔记暂时还没有准备好，请稍后再试。",
  });

const formatTime = (value?: number) => {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
};

onMounted(() => {
  loadNotes();
  window.addEventListener("smartnotes:updated", loadNotes as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("smartnotes:updated", loadNotes as EventListener);
});
</script>
