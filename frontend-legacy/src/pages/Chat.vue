<template>
  <div class="flex flex-col min-h-screen lg:h-screen lg:min-h-0 lg:overflow-hidden w-full px-4 md:pl-60 md:pr-6 lg:pl-64 lg:pr-64">
    <div class="w-full max-w-6xl mx-auto flex-1 min-h-0">
      <div class="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6 mt-20 lg:mt-6 mb-16 lg:mb-6 lg:h-[calc(100dvh-3rem)] lg:min-h-0">
        <div class="space-y-4 lg:sticky lg:top-24 lg:self-start lg:h-[calc(100dvh-6rem)] flex flex-col min-h-0">
          <LearningFolderPanel class="shrink-0" />
          <ChatHistoryPanel class="min-h-0" />
        </div>
        <div class="min-w-0 lg:min-h-0 lg:flex lg:flex-col">
          <div
            ref="messageViewportRef"
            class="w-full p-4 pt-2 pb-10 lg:pb-4 lg:flex-1 lg:min-h-0 lg:overflow-y-auto custom-scroll"
          >
            <div class="max-w-[1080px] mx-auto">
              <div v-if="!list.length" class="min-h-[62vh] flex items-center">
                <div class="w-full max-w-4xl mx-auto">
                  <div class="flex flex-col items-center text-center gap-3">
                    <div
                      class="size-16 rounded-3xl border shadow-[0_18px_40px_rgba(15,23,42,0.14)] flex items-center justify-center"
                      :class="isTeacherLanding ? 'bg-gradient-to-br from-sky-500/18 to-cyan-400/26 border-sky-400/25 text-sky-500' : 'bg-gradient-to-br from-amber-400/18 to-yellow-300/26 border-amber-300/35 text-amber-500'"
                    >
                      <svg viewBox="0 0 24 24" class="size-8" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5A3.5 3.5 0 0 1 17 16.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" />
                      </svg>
                    </div>
                    <h1 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">{{ landingTitle }}</h1>
                    <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                      {{ landingDescription }}
                    </p>
                  </div>

                  <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                    <button
                      v-for="q in quickQuestions"
                      :key="q"
                      type="button"
                      class="px-4 py-2 rounded-full border border-sky-300/45 bg-white/82 text-sm font-medium text-slate-800 shadow-[0_10px_18px_rgba(15,23,42,0.08)] hover:bg-sky-50 transition-colors cursor-pointer"
                      @click="quickAsk(q)"
                    >
                      {{ q }}
                    </button>
                  </div>

                  <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div
                      v-for="item in landingFeatureCards"
                      :key="item.title"
                      class="rounded-3xl p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]"
                      :class="landingCardClass"
                    >
                      <div class="flex items-center gap-3">
                        <span class="size-10 rounded-2xl flex items-center justify-center" :class="item.tone">
                          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
                          </svg>
                        </span>
                        <div>
                          <div class="text-sm font-semibold text-[color:var(--app-text)]">{{ item.title }}</div>
                          <div class="text-xs text-[color:var(--nav-text-muted)]">{{ item.desc }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="list.length" class="space-y-6">
                <div v-for="(m, i) in list" :key="i" class="w-full flex justify-start">
                  <div v-if="m.role === 'assistant'" class="w-full mx-auto rounded-3xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-[0_10px_30px_rgba(0,0,0,0.45)] ring-1 ring-black/10 backdrop-blur px-6 md:px-8 py-6 md:py-8 max-w-[min(100%,1000px)]">
                    <div class="animate-[fadeIn_300ms_ease-out] leading-7 md:leading-8">
                      <MarkdownView :md="m.content" />
                    </div>
                  </div>
                  <div v-else class="flex max-w-[85%] flex-col items-start gap-3">
                    <div class="inline-block bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-2xl px-4 py-3">
                      <div class="text-[color:var(--app-text)] whitespace-pre-wrap leading-relaxed">{{ m.content }}</div>
                    </div>
                    <ChatThinkingIndicator
                      v-if="pendingVisible && i === pendingAnchorIndex"
                      emoji="🤔"
                      title="AI 正在思考回答"
                      :description="pendingStatusText"
                    />
                  </div>
                </div>

              </div>
              <div ref="scrollRef" class="h-1 w-full" />
            </div>
          </div>
          <div class="max-w-[1080px] mx-auto lg:w-full lg:shrink-0">
            <Composer
              inline
              :disabled="busy"
              :onSend="sendFollowup"
              :onSelectInclude="setIncludeMaterials"
              :responseLengthText="responseLengthText"
              :showLength="showLength"
              :lengths="lengths"
              :onToggleLength="toggleLength"
              :onSelectLength="selectLength"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getUserScopedStorageKey } from "../lib/userStorage";
import {
  chatJSON,
  connectChatStream,
  connectTaskEvents,
  getChatDetail,
  type FlashCard,
  type ChatEvent,
  type ChatMessage,
  podcastStart,
} from "../lib/api";
import MarkdownView from "../components/Chat/MarkdownView.vue";
import Composer from "../components/Chat/Composer.vue";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import ChatHistoryPanel from "../components/Chat/ChatHistoryPanel.vue";
import ChatThinkingIndicator from "../components/Chat/ChatThinkingIndicator.vue";
import { useCompanionStore } from "../stores/companion";
import { useRoleStore } from "../stores/role";

type LocationState = {
  chatId?: string;
  q?: string;
  answer?: string | { html?: string; answer?: string; flashcards?: FlashCard[]; topic?: string };
  flashcards?: FlashCard[];
  length?: "Short" | "Medium" | "Long";
};

const route = useRoute();
const router = useRouter();
const companion = useCompanionStore();
const roleStore = useRoleStore();

const chatId = ref("");
const messages = ref<ChatMessage[]>([]);
const cards = ref<FlashCard[]>([]);
const busy = ref(false);
const connecting = ref(false);
const awaitingAnswer = ref(false);
const generationPhase = ref("");
const topic = ref("");

const streamRef = ref<{ close: () => void } | null>(null);
const wsRef = ref<WebSocket | null>(null);
const connectedChatId = ref("");
const streamMode = ref<"sse" | "ws" | "">("");
const fallbackAttempted = ref(false);
const receivedStreamEvent = ref(false);
const streamingAssistantIndex = ref<number | null>(null);
const messageViewportRef = ref<HTMLDivElement | null>(null);
const scrollRef = ref<HTMLDivElement | null>(null);

const state = computed<LocationState>(() => (((route as any).state || {}) as LocationState));
const initialChatId = computed(() => (route.query.chatId as string) || state.value.chatId || "");
const initialQuestion = computed(() => (route.query.q as string) || state.value.q || "");
const initialLength = computed(() => (route.query.length as string) || state.value.length || "Short");
const responseLength = ref<"Short" | "Medium" | "Long">("Short");
const responseLengthText = ref<"简短" | "中等" | "详细">("简短");
const showLength = ref(false);
const includeMaterials = ref(false);

const isTeacherPage = computed(() => route.path.startsWith("/teacher/"));
const LEARNING_FOLDER_KEY = computed(() =>
  getUserScopedStorageKey(isTeacherPage.value ? "edumind-learning-folder-teacher" : "edumind-learning-folder")
);

provide("chatRole", computed(() => (isTeacherPage.value ? "teacher" : "student")));
provide("chatBasePath", computed(() => (isTeacherPage.value ? "/teacher/chat" : "/chat")));
provide("learningFolderKey", LEARNING_FOLDER_KEY);

const list = computed(() => (Array.isArray(messages.value) ? messages.value : []));
const isTeacherLanding = computed(() => isTeacherPage.value || roleStore.role === "teacher");
const landingTitle = computed(() => (isTeacherLanding.value ? "教师工作台对话" : "学生学习对话"));
const landingDescription = computed(() =>
  isTeacherLanding.value
    ? "围绕课程资料生成教学目标、课堂提纲、互动问题与即时测验，支持多轮连续追问，适合备课前快速整理思路。"
    : "围绕学习资料做总结、答疑、例题讲解与错因分析，支持连续追问与不同回复深度，适合课后巩固与自测。"
);
const landingCardClass = computed(() =>
  isTeacherLanding.value
    ? "border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40"
    : "border border-amber-200/60 dark:border-amber-800/50 bg-gradient-to-br from-amber-50 to-yellow-50/90 dark:from-amber-950/50 dark:to-yellow-950/40"
);

const quickQuestions = computed(() =>
  isTeacherLanding.value
    ? ["本节课教学目标与重难点", "根据资料出5道测验题", "整理课堂板书与例题", "设计课堂互动提问"]
    : ["用通俗话总结这一章", "核心概念与公式梳理", "出几道题并讲解", "这里不懂请再讲一遍"]
);

const teacherFeatureCards = computed(() => [
  {
    title: "教学目标梳理",
    desc: "快速整理三维目标、重难点与课堂推进逻辑。",
    tone: "bg-amber-500/15 text-amber-500",
    icon: "M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7",
  },
  {
    title: "资料串讲设计",
    desc: "围绕挂载资料生成讲解提纲、板书与关键例题。",
    tone: "bg-sky-500/15 text-sky-500",
    icon: "M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z",
  },
  {
    title: "课堂互动问题",
    desc: "支持连续追问，方便补充课堂发问与师生互动脚本。",
    tone: "bg-emerald-500/15 text-emerald-500",
    icon: "M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z",
  },
  {
    title: "回复深度可控",
    desc: "支持简短、中等、详细三档输出，适配不同备课节奏。",
    tone: "bg-violet-500/15 text-violet-500",
    icon: "M12 5.25v13.5m6-6.75H6",
  },
]);

const studentFeatureCards = computed(() => [
  {
    title: "资料总结答疑",
    desc: "围绕学习资料做总结、问答与知识点拆解。",
    tone: "bg-amber-500/15 text-amber-500",
    icon: "M3 6.75A1.5 1.5 0 0 1 4.5 5.25h5l1.5 1.5H19.5A1.5 1.5 0 0 1 21 8.25v9A1.5 1.5 0 0 1 19.5 18.75h-15A1.5 1.5 0 0 1 3 17.25v-10.5Z",
  },
  {
    title: "概念公式梳理",
    desc: "快速提炼重点概念、公式与常见易错点。",
    tone: "bg-sky-500/15 text-sky-500",
    icon: "M4.5 7.5h15M4.5 12h10.5M4.5 16.5h7",
  },
  {
    title: "例题与错因分析",
    desc: "支持连续追问，方便补充解题思路与错因复盘。",
    tone: "bg-emerald-500/15 text-emerald-500",
    icon: "M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z",
  },
  {
    title: "回复深度可控",
    desc: "支持简短、中等、详细三档输出，适配不同学习节奏。",
    tone: "bg-violet-500/15 text-violet-500",
    icon: "M12 5.25v13.5m6-6.75H6",
  },
]);

const landingFeatureCards = computed(() => (isTeacherLanding.value ? teacherFeatureCards.value : studentFeatureCards.value));

const lengths = [
  { key: "Short", label: "简短" },
  { key: "Medium", label: "中等" },
  { key: "Long", label: "详细" },
] as const;

const latestAssistantContent = computed(() => {
  for (let i = list.value.length - 1; i >= 0; i -= 1) {
    if (list.value[i].role === "assistant") return list.value[i].content;
  }
  return "";
});

const pendingVisible = computed(() => awaitingAnswer.value || connecting.value);
const pendingAnchorIndex = computed(() => {
  for (let i = list.value.length - 1; i >= 0; i -= 1) {
    if (list.value[i].role === "user") return i;
  }
  return -1;
});
const pendingStatusText = computed(() => {
  if (connecting.value) return "问题已经收到，正在连接回答通道";
  const phaseText: Record<string, string> = {
    queued: "请求已进入生成队列",
    preparing: "正在整理对话上下文",
    retrieving: "正在检索资料库内容",
    generating: "正在调用模型生成回答",
    streaming: "正在接收模型回答",
  };
  return phaseText[generationPhase.value] || "问题已经收到，正在整理答案和上下文";
});

const extractFirstJsonObject = (s: string) => {
  let depth = 0;
  let start = -1;
  for (let i = 0; i < s.length; i += 1) {
    const ch = s[i];
    if (ch === "{") {
      if (depth === 0) start = i;
      depth += 1;
    } else if (ch === "}") {
      depth -= 1;
      if (depth === 0 && start !== -1) return s.slice(start, i + 1);
    }
  }
  return "";
};

const normalizePayload = (payload: unknown): { md: string; flashcards: FlashCard[]; topic?: string } => {
  if (typeof payload === "string") {
    const s = payload.trim();
    if (s.startsWith("{") && s.endsWith("}")) {
      try {
        const obj = JSON.parse(s);
        return {
          md: String(obj?.answer || ""),
          flashcards: Array.isArray(obj?.flashcards) ? obj.flashcards : [],
          topic: typeof obj?.topic === "string" ? obj.topic : undefined,
        };
      } catch {
        return { md: s, flashcards: [] };
      }
    }
    const inner = extractFirstJsonObject(s);
    if (inner) {
      try {
        const obj = JSON.parse(inner);
        return {
          md: String(obj?.answer || ""),
          flashcards: Array.isArray(obj?.flashcards) ? obj.flashcards : [],
          topic: typeof obj?.topic === "string" ? obj.topic : undefined,
        };
      } catch {
        return { md: s, flashcards: [] };
      }
    }
    return { md: s, flashcards: [] };
  }
  if (payload && typeof payload === "object") {
    const obj = payload as any;
    return {
      md: String(obj?.answer || obj?.html || ""),
      flashcards: Array.isArray(obj?.flashcards) ? obj.flashcards : [],
      topic: typeof obj?.topic === "string" ? obj.topic : undefined,
    };
  }
  return { md: "", flashcards: [] };
};

const deriveTopicFromMarkdown = (md: string) => {
  const m = md.match(/^\s*#{1,6}\s+(.+?)\s*$/m);
  return m ? m[1].trim() : "";
};

const normalizeLength = (value: string) => {
  if (value === "Long" || value === "Medium" || value === "Short") return value;
  return "Short";
};

const loadLearningFolderIds = () => {
  try {
    const key = LEARNING_FOLDER_KEY.value;
    const raw = localStorage.getItem(key);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [] as string[];
  }
};

const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
  const viewport = messageViewportRef.value;
  if (viewport) {
    viewport.scrollTo({ top: viewport.scrollHeight, behavior });
    return;
  }
  scrollRef.value?.scrollIntoView({ behavior, block: "end" });
};

const closeSocket = () => {
  try {
    wsRef.value?.close();
  } catch {
    // Ignore socket close races during route transitions.
  }
  wsRef.value = null;
};

const closeStream = () => {
  try {
    streamRef.value?.close();
  } catch {
    // EventSource/WebSocket may already be closed.
  }
  streamRef.value = null;
  closeSocket();
  connectedChatId.value = "";
  streamMode.value = "";
};

const lastUserIndex = () => {
  for (let i = list.value.length - 1; i >= 0; i -= 1) {
    if (list.value[i].role === "user") return i;
  }
  return -1;
};

const assistantAfterLastUserIndex = () => {
  const anchor = lastUserIndex();
  for (let i = list.value.length - 1; i > anchor; i -= 1) {
    if (list.value[i].role === "assistant") return i;
  }
  return -1;
};

const ensureStreamingAssistant = () => {
  const existing = streamingAssistantIndex.value ?? assistantAfterLastUserIndex();
  if (existing >= 0 && list.value[existing]?.role === "assistant") {
    streamingAssistantIndex.value = existing;
    return existing;
  }
  const next = [...list.value, { role: "assistant" as const, content: "", at: Date.now() }];
  messages.value = next;
  streamingAssistantIndex.value = next.length - 1;
  return streamingAssistantIndex.value;
};

const updateAssistantContent = (content: string, replace = false) => {
  const index = ensureStreamingAssistant();
  const next = [...list.value];
  const current = next[index];
  if (!current || current.role !== "assistant") return;
  next[index] = {
    ...current,
    content: replace ? content : `${current.content || ""}${content}`,
    at: Date.now(),
  };
  messages.value = next;
  setTimeout(() => scrollToBottom("smooth"), 0);
};

const finishAnswer = () => {
  awaitingAnswer.value = false;
  connecting.value = false;
  busy.value = false;
  generationPhase.value = "";
  streamingAssistantIndex.value = null;
  streamRef.value?.close();
  streamRef.value = null;
  closeSocket();
  streamMode.value = "";
};

const handleChatEvent = (m: ChatEvent | any) => {
  if (!m?.type) return;
  if (m.type !== "ready" && m.type !== "ping") receivedStreamEvent.value = true;

  if (m.type === "ready") {
    connecting.value = false;
    return;
  }
  if (m.type === "phase") {
    generationPhase.value = String(m.value || "");
    awaitingAnswer.value = true;
    busy.value = true;
    connecting.value = false;
    return;
  }
  if (m.type === "ping") {
    awaitingAnswer.value = true;
    busy.value = true;
    connecting.value = false;
    return;
  }
  if (m.type === "delta") {
    const delta = String(m.delta || "");
    if (!delta) return;
    generationPhase.value = "streaming";
    awaitingAnswer.value = false;
    busy.value = true;
    connecting.value = false;
    updateAssistantContent(delta);
    return;
  }
  if (m.type === "answer") {
    const norm = normalizePayload(m.answer);
    if (norm.md) updateAssistantContent(norm.md, true);
    if (norm.flashcards.length) cards.value = norm.flashcards;
    if (norm.topic) topic.value = norm.topic;
    else if (norm.md && !topic.value) topic.value = deriveTopicFromMarkdown(norm.md);
    awaitingAnswer.value = false;
    connecting.value = false;
    return;
  }
  if (m.type === "done") {
    finishAnswer();
    return;
  }
  if (m.type === "error") {
    const errText = String(m.error || "");
    if (streamMode.value === "sse" && errText === "stream_error" && busy.value && !fallbackAttempted.value) {
      fallbackAttempted.value = true;
      const cid = connectedChatId.value || chatId.value;
      try {
        streamRef.value?.close();
      } catch {
        // Ignore close races while switching transports.
      }
      streamRef.value = null;
      if (cid) connectChatWebSocket(cid);
      return;
    }
    if (errText === "stream_error" && !receivedStreamEvent.value) {
      connecting.value = false;
      return;
    }
    updateAssistantContent(`抱歉，生成失败：${errText || "模型生成失败，请稍后重试"}`, true);
    finishAnswer();
  }
};

const connectChatWebSocket = (cid: string) => {
  closeSocket();
  streamMode.value = "ws";
  connecting.value = true;
  const { ws, close } = connectChatStream(cid, handleChatEvent);
  wsRef.value = ws;
  streamRef.value = { close };
  ws.onopen = () => (connecting.value = false);
  ws.onclose = () => {
    if (busy.value || awaitingAnswer.value) return;
    if (wsRef.value === ws) {
      wsRef.value = null;
    }
  };
};

const connectChat = (cid: string) => {
  if (!cid) return;
  if (connectedChatId.value === cid && streamRef.value) return;
  closeStream();
  connectedChatId.value = cid;
  streamMode.value = "sse";
  fallbackAttempted.value = false;
  receivedStreamEvent.value = false;
  connecting.value = true;
  streamRef.value = connectTaskEvents<ChatEvent>("chat", cid, handleChatEvent);
};

const loadChatsIfEmpty = async () => {
  if (initialChatId.value || initialQuestion.value) return;
  connecting.value = false;
  chatId.value = "";
  router.replace({ path: isTeacherPage.value ? "/teacher/chat" : "/chat" });
};

const loadChat = async (cid: string) => {
  if (!cid) return;
  try {
    const res = await getChatDetail(cid);
    if (res?.ok && Array.isArray(res.messages)) {
      const normalized = res.messages.map((m) =>
        m.role === "assistant" ? { ...m, content: normalizePayload((m as any).content).md } : m
      );
      messages.value = normalized as ChatMessage[];
      for (let i = normalized.length - 1; i >= 0; i -= 1) {
        const raw = (res.messages[i] as any)?.content;
        if (normalized[i].role === "assistant") {
          const n = normalizePayload(raw);
          if (n.flashcards.length) cards.value = n.flashcards;
          if (n.topic) topic.value = n.topic;
          else if (n.md) topic.value = deriveTopicFromMarkdown(n.md);
          break;
        }
      }
      setTimeout(() => scrollToBottom("auto"), 0);
    }
  } catch {
    return;
  }
};

const hydrateState = () => {
  chatId.value = initialChatId.value || "";
  responseLength.value = normalizeLength(initialLength.value);
  responseLengthText.value = responseLength.value === "Long" ? "详细" : responseLength.value === "Medium" ? "中等" : "简短";
  if (state.value.answer) {
    const init = normalizePayload(state.value.answer);
    const seed: ChatMessage[] = [];
    if (initialQuestion.value) seed.push({ role: "user", content: initialQuestion.value, at: Date.now() });
    if (init.md) seed.push({ role: "assistant", content: init.md, at: Date.now() });
    if (seed.length) messages.value = seed;
    if (init.flashcards?.length || state.value.flashcards?.length)
      cards.value = init.flashcards?.length ? init.flashcards : state.value.flashcards || [];
    if (init.topic) topic.value = init.topic || "";
    else if (init.md) topic.value = deriveTopicFromMarkdown(init.md);
  } else if (initialQuestion.value) {
    if (!messages.value.length) messages.value = [{ role: "user", content: initialQuestion.value, at: Date.now() }];
    awaitingAnswer.value = true;
  }
};

const sendFollowup = async (text: string) => {
  const trimmed = text.trim();
  if (!trimmed || busy.value) return;
  messages.value = [...list.value, { role: "user", content: trimmed, at: Date.now() }];
  awaitingAnswer.value = true;
  busy.value = true;
  generationPhase.value = "queued";
  streamingAssistantIndex.value = null;
  try {
    closeStream();
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value;
    const r = await chatJSON({
      q: trimmed,
      chatId: chatId.value || undefined,
      length: responseLength.value,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      role: isTeacherPage.value ? "teacher" : "student",
    });
    const nextChatId = r?.chatId || chatId.value;
    if (r?.chatId && r.chatId !== chatId.value) {
      chatId.value = r.chatId;
      router.replace({
        path: isTeacherPage.value ? "/teacher/chat" : "/chat",
        query: { chatId: r.chatId },
      });
    }
    if (nextChatId) {
      connectChat(nextChatId);
    }
  } catch (err: any) {
    const errText = err?.message || "提交问题失败，请稍后重试";
    updateAssistantContent(`抱歉，${errText}`, true);
    finishAnswer();
  } finally {
    setTimeout(() => scrollToBottom("smooth"), 0);
  }
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const toggleLength = () => {
  showLength.value = !showLength.value;
};

const labelForLength = (key: "Short" | "Medium" | "Long"): "简短" | "中等" | "详细" => {
  if (key === "Long") return "详细";
  if (key === "Medium") return "中等";
  return "简短";
};

const selectLength = (next: string, label: string) => {
  const normalized = normalizeLength(String(next));
  responseLength.value = normalized;
  responseLengthText.value = (label === "简短" || label === "中等" || label === "详细") ? label : labelForLength(normalized);
  showLength.value = false;
};

const quickAsk = (q: string) => {
  if (busy.value) return;
  sendFollowup(q);
};

const startQuiz = () => {
  const t = topic.value || deriveTopicFromMarkdown(latestAssistantContent.value) || "General";
  router.push({ path: "/quiz", query: { topic: t }, state: { topic: t } });
};

const createPodcast = async () => {
  try {
    const topicContent = latestAssistantContent.value || topic.value || "Generated from chat";
    const response = await podcastStart({ topic: topicContent });
    router.push({ path: "/tools", state: { podcastPid: response.pid, podcastTopic: topicContent } });
  } catch {
    return;
  }
};

onMounted(async () => {
  await loadChatsIfEmpty();
  hydrateState();
});

watch(chatId, async (next, prev) => {
  if (!next) {
    closeStream();
    return;
  }
  if (next === prev) return;
  await loadChat(next);
  if (list.value.length && list.value[list.value.length - 1]?.role === "user") {
    awaitingAnswer.value = true;
    busy.value = true;
    connectChat(next);
  }
});

watch(
  () => route.query.chatId,
  async (next) => {
    const cid = (next as string) || state.value.chatId || "";
    if (!cid) {
      chatId.value = "";
      messages.value = [];
      cards.value = [];
      topic.value = "";
      awaitingAnswer.value = false;
      busy.value = false;
      generationPhase.value = "";
      streamingAssistantIndex.value = null;
      closeStream();
      return;
    }
    if (cid === chatId.value) return;
    chatId.value = cid;
  }
);

watch(list, () => {
  setTimeout(() => scrollToBottom("smooth"), 0);
});

watch([chatId, latestAssistantContent, topic], () => {
  if (latestAssistantContent.value) {
    const docTitle = topic.value || deriveTopicFromMarkdown(latestAssistantContent.value) || "Study Topic";
    const docId = chatId.value ? `chat:${chatId.value}` : "chat:current";
    companion.setDocument({ id: docId, title: docTitle, text: latestAssistantContent.value });
  } else {
    companion.setDocument(null);
  }
});

onBeforeUnmount(() => {
  companion.setDocument(null);
  closeStream();
});
</script>
