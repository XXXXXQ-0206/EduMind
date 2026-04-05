<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <NoteHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="mb-6 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <h1 class="flex items-center gap-3 text-2xl font-semibold text-[color:var(--app-text)]">智能笔记</h1>
            </div>
          </div>

          <div
            v-if="viewState === 'composer'"
            class="flex min-h-[62vh] flex-col items-center justify-center"
          >
            <div class="mx-auto w-full max-w-3xl">
              <div class="flex flex-col items-center gap-3 text-center">
                <div class="flex size-16 items-center justify-center rounded-3xl border border-sky-400/30 bg-gradient-to-br from-sky-500/20 to-cyan-400/30 shadow-[0_18px_40px_rgba(14,165,233,0.25)]">
                  <svg viewBox="0 0 24 24" class="size-8 text-sky-500" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v10.5H5.25z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75v-1.5h7.5v1.5" />
                  </svg>
                </div>
                <h2 class="text-2xl font-semibold text-[color:var(--app-text)] md:text-3xl">打造你的专属学习笔记</h2>
                <p class="max-w-2xl text-sm text-[color:var(--nav-text-muted)] md:text-base">
                  输入主题即可生成康奈尔结构笔记，支持资料引用与长度选择，随时下载留存。
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="cursor-pointer rounded-full border border-sky-400/30 bg-white/80 px-4 py-2 text-sm text-slate-800 shadow-[0_8px_16px_rgba(15,23,42,0.08)] transition-colors hover:bg-white"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v10.5H5.25z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">康奈尔结构</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">重点、总结、问题一体化整理。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12a7.5 7.5 0 1 1 15 0 7.5 7.5 0 0 1-15 0Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">资料引用</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可基于上传内容生成更贴合的笔记。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15M4.5 12h10.5M4.5 17.25h7" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">长度可选</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">粗略、中等、详细三档可调。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="flex size-10 items-center justify-center rounded-2xl bg-indigo-500/15 text-indigo-500">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">一键下载</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">生成后即可下载 PDF 保存。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <NoteTopicBar
                  :key="noteBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="() => start(topic)"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectLength="setLength"
                  :lengthValue="length"
                  :isLoading="false"
                />
              </div>
            </div>
          </div>

          <div v-else-if="viewState === 'waiting'" class="mt-10 space-y-4">
            <GenerationStatusCard
              emoji="📒"
              tone="amber"
              :title="waitingTitle"
              :description="waitingDescription"
              :phase="notesPhase"
              :steps="notesGenerationSteps"
            />

            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">当前任务</div>
                  <div class="mt-1 text-lg font-semibold text-[color:var(--app-text)]">{{ topic || "未命名笔记" }}</div>
                  <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span class="rounded-full border border-amber-300/50 bg-amber-100/70 px-2.5 py-1 font-semibold text-amber-800">
                      {{ noteStatusLabel }}
                    </span>
                    <span v-if="noteId" class="rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 px-2.5 py-1 text-[color:var(--nav-text-muted)]">
                      ID {{ shortNoteId }}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-4 py-2 text-sm font-medium text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]"
                  @click="createNewNote"
                >
                  新建笔记
                </button>
              </div>

              <div class="mt-4 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4 text-sm text-[color:var(--nav-text)]">
                {{ friendlyNoteError || waitingHint }}
              </div>
            </div>
          </div>

          <div v-else class="space-y-6">
            <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] p-6 shadow-[0_16px_36px_rgba(0,0,0,0.3)]">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">智能笔记</div>
                  <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ notesPayload?.title || topic || "未命名笔记" }}</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <a
                    v-if="fileUrl"
                    :href="fileUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 rounded-full border border-emerald-300/60 bg-gradient-to-r from-emerald-400 to-lime-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 shadow-[0_12px_24px_rgba(16,185,129,0.35)] transition-all hover:brightness-110"
                  >
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5h15" />
                    </svg>
                    下载 PDF
                  </a>
                  <button
                    type="button"
                    class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-4 py-2.5 text-sm font-medium text-[color:var(--app-text)] transition-colors hover:bg-[color:var(--nav-hover-bg-strong)]"
                    @click="createNewNote"
                  >
                    新建笔记
                  </button>
                </div>
              </div>
            </div>

            <div class="grid gap-4">
              <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                <div class="text-sm font-semibold text-[color:var(--app-text)]">正文内容</div>
                <div class="smartnotes-markdown mt-3 leading-relaxed text-[color:var(--nav-text)]">
                  <MarkdownView :md="notesPayload?.notes || ''" />
                </div>
              </div>

              <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="text-sm font-semibold text-[color:var(--app-text)]">总结</div>
                  <div class="mt-3 whitespace-pre-wrap text-sm text-[color:var(--nav-text)]">
                    {{ notesPayload?.summary || "暂无" }}
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-6 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="text-sm font-semibold text-[color:var(--app-text)]">关键问题</div>
                  <ul v-if="notesPayload?.questions?.length" class="mt-3 space-y-2">
                    <li v-for="(q, i) in notesPayload.questions" :key="i" class="text-sm text-[color:var(--nav-text)]">
                      <div class="font-medium">Q{{ i + 1 }}：{{ q }}</div>
                      <div v-if="notesPayload?.answers?.[i]" class="mt-1 text-xs text-[color:var(--nav-text-muted)]">
                        A：{{ notesPayload.answers[i] }}
                      </div>
                    </li>
                  </ul>
                  <div v-else class="mt-3 text-sm text-[color:var(--nav-text-muted)]">暂无</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  connectSmartnotesStream,
  friendlyTaskMessage,
  getSmartNoteDetail,
  smartnotesStart,
  type GenerationRecordStatus,
  type SmartNoteMeta,
  type SmartNotesEvent,
  type SmartNotesPayload,
} from "../lib/api";
import { env } from "../config/env";
import { getAuthToken } from "../lib/auth";
import { getUserScopedStorageKey } from "../lib/userStorage";
import { getRouteState } from "../lib/routerState";
import MarkdownView from "../components/Chat/MarkdownView.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import NoteHistoryPanel from "../components/SmartNotes/NoteHistoryPanel.vue";
import NoteTopicBar from "../components/SmartNotes/NoteTopicBar.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

type NoteViewState = "composer" | "waiting" | "ready";

const route = useRoute();
const router = useRouter();

const passedNoteId = getRouteState<{ noteId?: string }>().noteId || "";
const initialNoteId = (route.query.noteId as string) || passedNoteId || "";

const topic = ref("");
const noteId = ref(initialNoteId);
const viewState = ref<NoteViewState>(initialNoteId ? "waiting" : "composer");
const notesPhase = ref("generating");
const noteStatus = ref<GenerationRecordStatus>("pending");
const noteError = ref("");
const includeMaterials = ref(false);
const length = ref<"rough" | "medium" | "detailed">("medium");
const fileUrl = ref<string | null>(null);
const notesPayload = ref<SmartNotesPayload | null>(null);
const noteBarKey = ref(0);
const quickTopics = ["生态系统", "函数与图像", "细胞结构", "数据结构基础"];
const notesGenerationSteps = [
  { key: "generating", label: "正在整理笔记" },
  { key: "notes", label: "正在补全正文" },
  { key: "file", label: "正在准备下载文件" },
];

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("pagelm-learning-folder"));
const closeRef = ref<null | (() => void)>(null);
const activeRunId = ref(0);
let detailPollTimer: number | null = null;

const shortNoteId = computed(() => (noteId.value ? noteId.value.slice(0, 8) : ""));
const noteStatusLabel = computed(() => {
  if (noteStatus.value === "ready") return "已完成";
  if (noteStatus.value === "error") return "生成失败";
  return "生成中";
});
const friendlyNoteError = computed(() =>
  noteError.value
    ? friendlyTaskMessage(noteError.value, { feature: "smartnotes" })
    : "",
);
const waitingTitle = computed(() => {
  if (noteStatus.value === "error") return "智能笔记未生成成功";
  if (notesPhase.value === "file") return "笔记内容已经准备好";
  if (notesPhase.value === "notes") return "正在整理可阅读的笔记";
  return "智能笔记正在生成";
});
const waitingDescription = computed(() => {
  if (noteStatus.value === "error") return "这次没有顺利完成，你可以直接重新开始。";
  return "提交后页面会一直停留在这里，准备好的内容会自动出现，不需要反复刷新。";
});
const waitingHint = computed(() => {
  if (noteStatus.value === "error") return "旧任务已停止等待。点击“新建笔记”即可重新开始。";
  if (notesPhase.value === "file") return "正文已经整理好，正在补上下载文件。";
  if (notesPhase.value === "notes") return "正在把重点、总结和问题整理成完整笔记。";
  return "内容生成中，请稍等，准备好后会自动展示。";
});

const notifyHistoryUpdated = (nextNoteId?: string) => {
  try {
    window.dispatchEvent(new CustomEvent("smartnotes:updated", { detail: { noteId: nextNoteId || noteId.value } }));
  } catch {
    return;
  }
};

const nextRunId = () => {
  activeRunId.value += 1;
  return activeRunId.value;
};

const isActiveRun = (runId: number) => activeRunId.value === runId;

const clearDetailPolling = () => {
  if (detailPollTimer !== null) {
    window.clearTimeout(detailPollTimer);
    detailPollTimer = null;
  }
};

const clearStream = () => {
  if (!closeRef.value) return;
  closeRef.value();
  closeRef.value = null;
};

const setTopic = (value: string) => {
  topic.value = value;
};

const onQuickTopic = (value: string) => {
  topic.value = value;
  void start(value);
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const setLength = (next: "rough" | "medium" | "detailed") => {
  length.value = next;
};

const loadLearningFolderIds = () => {
  try {
    const raw = localStorage.getItem(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [] as string[];
  }
};

const resetState = () => {
  nextRunId();
  clearDetailPolling();
  clearStream();
  viewState.value = "composer";
  topic.value = "";
  noteId.value = "";
  includeMaterials.value = false;
  length.value = "medium";
  fileUrl.value = null;
  notesPayload.value = null;
  noteStatus.value = "pending";
  noteError.value = "";
  notesPhase.value = "generating";
  noteBarKey.value += 1;
};

const createNewNote = () => {
  router.push({ path: "/smart-notes", query: { new: String(Date.now()) } });
};

const resolveNoteFileUrl = (raw?: string | null) => {
  if (!raw) return null;
  const value = String(raw).trim();
  if (!value) return null;
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

const applyNoteDetail = (id: string, meta: SmartNoteMeta, payload: SmartNotesPayload | null) => {
  noteId.value = meta.id || id;
  topic.value = meta.title || topic.value;
  length.value = (meta.length as "rough" | "medium" | "detailed") || length.value;
  fileUrl.value = resolveNoteFileUrl(meta.file || null);
  notesPayload.value = payload || null;
  noteStatus.value = meta.status || (meta.file || payload ? "ready" : "pending");
  noteError.value = meta.error || "";

  if (payload) notesPhase.value = "notes";
  if (meta.file) notesPhase.value = "file";

  notifyHistoryUpdated(id);

  if (payload || meta.file) {
    viewState.value = "ready";
    clearDetailPolling();
    return true;
  }

  viewState.value = "waiting";
  if (noteStatus.value === "error") {
    clearDetailPolling();
  }
  return false;
};

const fetchNoteDetail = async (id: string, runId: number) => {
  if (!id || !isActiveRun(runId)) return false;
  try {
    const res = await getSmartNoteDetail(id);
    if (!res?.ok || !isActiveRun(runId)) return false;
    return applyNoteDetail(id, res.note, res.notes || null);
  } catch {
    return false;
  }
};

const scheduleDetailPolling = (id: string, runId: number, delay = 2200) => {
  if (!id || !isActiveRun(runId)) return;
  clearDetailPolling();
  detailPollTimer = window.setTimeout(async () => {
    detailPollTimer = null;
    if (!isActiveRun(runId)) return;
    const ready = await fetchNoteDetail(id, runId);
    if (!isActiveRun(runId) || ready || noteStatus.value === "error") return;
    scheduleDetailPolling(id, runId);
  }, delay);
};

const openExistingNote = async (id: string) => {
  if (!id) return;
  const runId = nextRunId();
  clearDetailPolling();
  clearStream();
  viewState.value = "waiting";
  noteId.value = id;
  fileUrl.value = null;
  notesPayload.value = null;
  noteStatus.value = "pending";
  noteError.value = "";
  notesPhase.value = "generating";
  const ready = await fetchNoteDetail(id, runId);
  if (!isActiveRun(runId) || ready || String(noteStatus.value) === "error") return;
  scheduleDetailPolling(id, runId, 0);
};

const start = async (input: string) => {
  const trimmed = input.trim();
  if (!trimmed) return;

  const runId = nextRunId();
  clearDetailPolling();
  clearStream();
  viewState.value = "waiting";
  topic.value = trimmed;
  noteStatus.value = "pending";
  noteError.value = "";
  notesPhase.value = "generating";
  fileUrl.value = null;
  notesPayload.value = null;

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const res = await smartnotesStart({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      length: length.value,
    });
    if (!res?.noteId) throw new Error("noteId missing");
    if (!isActiveRun(runId)) return;

    noteId.value = res.noteId;
    notifyHistoryUpdated(res.noteId);
    scheduleDetailPolling(res.noteId, runId, 1200);

    const { close } = connectSmartnotesStream(res.noteId, (ev: SmartNotesEvent) => {
      if (!isActiveRun(runId)) return;
      if (ev.type === "phase" && ev.value) {
        notesPhase.value = ev.value;
      }
      if (ev.type === "notes") {
        notesPhase.value = "notes";
        void fetchNoteDetail(res.noteId, runId);
      }
      if (ev.type === "file") {
        notesPhase.value = "file";
        void fetchNoteDetail(res.noteId, runId);
      }
      if (ev.type === "error" && ev.error && !noteError.value) {
        noteError.value = ev.error;
      }
      if (ev.type === "done" || ev.type === "error" || ev.type === "close") {
        scheduleDetailPolling(res.noteId, runId, 0);
      }
    });
    closeRef.value = () => {
      close();
      closeRef.value = null;
    };

    router.replace({ path: "/smart-notes", query: { noteId: res.noteId }, state: { noteId: res.noteId } });
  } catch (error) {
    if (!isActiveRun(runId)) return;
    noteStatus.value = "error";
    noteError.value = error instanceof Error ? error.message : "笔记启动失败";
  }
};

onMounted(() => {
  if (initialNoteId) {
    void openExistingNote(initialNoteId);
  }
});

watch(
  () => route.query.noteId,
  async (next) => {
    const id = (next as string) || getRouteState<{ noteId?: string }>().noteId || "";
    if (!id) {
      resetState();
      return;
    }
    if (id === noteId.value && viewState.value !== "composer") return;
    await openExistingNote(id);
  },
);

watch(
  () => route.query.new,
  (next) => {
    if (!next || route.path !== "/smart-notes") return;
    resetState();
  },
);

onBeforeUnmount(() => {
  clearDetailPolling();
  clearStream();
});
</script>
