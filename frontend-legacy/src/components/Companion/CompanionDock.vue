<template>
  <div>
    <button
      v-if="!open"
      type="button"
      @click="setOpen(true)"
      class="fixed bottom-6 right-6 z-40 px-4 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium shadow-lg shadow-blue-500/30 transition-colors"
    >
      学习助手
    </button>

    <div
      :class="[
        'fixed bottom-6 right-6 z-40 w-[min(360px,calc(100vw-2rem))] max-h-[min(85vh,640px)] rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)] backdrop-blur-xl shadow-2xl shadow-black/30 transition-all duration-300',
        open ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-4 pointer-events-none'
      ]"
    >
      <div class="flex items-start justify-between gap-3 px-5 pt-5 pb-3 border-b border-white/5">
        <div>
          <div class="text-xs font-semibold uppercase tracking-wide text-blue-200/80 mb-1">AI助手</div>
          <div class="text-white text-base font-medium leading-snug">{{ headerTitle }}</div>
          <div v-if="document?.filePath" class="text-[11px] text-stone-400 mt-1 truncate" :title="document.filePath">
            上下文: {{ document.filePath }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span
            :class="[
              'inline-flex items-center gap-1 px-2 py-1 rounded-full text-[11px]',
              hasDocument ? 'bg-emerald-500/10 text-emerald-300' : 'bg-white/5 text-[color:var(--nav-text-muted)]'
            ]"
          >
            <span class="w-2 h-2 rounded-full bg-current" />
            {{ hasDocument ? '上下文关联' : '无文档' }}
          </span>
          <button
            type="button"
            @click="setOpen(false)"
            class="p-2 rounded-full hover:bg-white/10 text-stone-300 transition-colors"
            aria-label="关闭助手"
          >
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" class="size-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 7l6 6m0-6-6 6" />
            </svg>
          </button>
        </div>
      </div>

      <div ref="bodyRef" class="px-5 py-4 space-y-4 overflow-y-auto custom-scroll">
        <div v-if="!hasDocument" class="text-sm text-stone-400">
          打开笔记或主题以解锁助手。它将仅使用该文档的内容进行回答。
        </div>

        <div v-if="hasDocument && messages.length === 0" class="space-y-3">
          <div class="text-sm text-stone-300 leading-relaxed">
            需要快速总结、测验或解释？询问有关当前文档的任何内容，我会基于该上下文回答。
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="suggestion in defaultSuggestions"
              :key="suggestion"
              type="button"
              :disabled="disabled"
              @click="send(suggestion)"
              class="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-[color:var(--nav-text)] hover:border-blue-400/60 hover:text-white transition-colors disabled:opacity-60"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <div v-for="msg in messages" :key="msg.id" :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
          <div
            :class="[
              'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
              msg.role === 'user' ? 'bg-blue-500/10 border border-blue-400/30 text-blue-50' : 'bg-white/5 border border-white/10 text-[color:var(--nav-text)]'
            ]"
          >
            <div v-if="msg.role === 'assistant'" class="space-y-3">
              <MarkdownView :md="msg.content" />
              <div v-if="msg.flashcards?.length" class="rounded-xl border border-blue-400/30 bg-blue-500/5 px-3 py-2">
                <div class="text-xs uppercase tracking-wide text-blue-200 mb-2">闪卡</div>
                <ul class="space-y-2 text-sm text-blue-50">
                  <li v-for="(card, idx) in msg.flashcards.slice(0, 4)" :key="`${msg.id}-card-${idx}`">
                    <div class="font-semibold">Q: {{ card.q }}</div>
                    <div class="text-sky-100/90">A: {{ card.a }}</div>
                  </li>
                  <li v-if="msg.flashcards.length > 4" class="text-xs text-blue-200/80">
                    此回答中还有 {{ msg.flashcards.length - 4 }} 张闪卡。
                  </li>
                </ul>
              </div>
            </div>
            <div v-else class="whitespace-pre-wrap">{{ msg.content }}</div>
          </div>
        </div>

        <div v-if="busy" class="flex justify-start">
          <div class="px-4 py-2 rounded-2xl bg-white/5 border border-white/10 text-xs text-[color:var(--nav-text-muted)] animate-pulse">
            思考中…
          </div>
        </div>

        <div v-if="error" class="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">
          {{ error }}
        </div>
      </div>

      <div class="px-5 pb-5 pt-3 border-t border-white/5">
        <div class="flex items-center gap-2">
          <input
            v-model="input"
            :placeholder="hasDocument ? '询问有关此文档的问题…' : '打开文档以开始'"
            :disabled="disabled && !hasDocument"
            class="flex-1 px-4 py-2.5 rounded-2xl bg-white/5 border border-white/10 text-sm text-[color:var(--app-text)] placeholder-[color:var(--nav-text-muted)] focus:border-blue-400/60 focus:ring-2 focus:ring-blue-500/30 disabled:opacity-50"
            @keydown.enter.exact.prevent="send()"
          />
          <button
            type="button"
            @click="send()"
            :disabled="disabled || !input.trim()"
            class="px-4 py-2.5 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { companionAsk, type FlashCard } from "../../lib/api";
import MarkdownView from "../Chat/MarkdownView.vue";
import { useCompanionStore } from "../../stores/companion";

const defaultSuggestions = ["总结关键观点", "快速测验", "新手解释"];

type CompanionMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  at: number;
  flashcards?: FlashCard[];
  topic?: string;
};

const store = useCompanionStore();
const input = ref("");
const messages = ref<CompanionMessage[]>([]);
const busy = ref(false);
const error = ref<string | null>(null);
const bodyRef = ref<HTMLDivElement | null>(null);

const document = computed(() => store.document);
const open = computed(() => store.open);
const hasDocument = computed(() => store.hasDocument);

const headerTitle = computed(() => {
  if (document.value?.title) return document.value.title;
  if (document.value?.filePath) return document.value.filePath.split(/[\\/]/).pop() || "Document";
  return "Study Companion";
});

const setOpen = (value: boolean) => {
  store.open = value;
};

const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const toHistoryPayload = (msgs: CompanionMessage[]) =>
  msgs.map((msg) => ({ role: msg.role, content: msg.content }));

const disabled = computed(() => !hasDocument.value || busy.value);

const scrollToBottom = async () => {
  await nextTick();
  if (!open.value || !bodyRef.value) return;
  bodyRef.value.scrollTop = bodyRef.value.scrollHeight;
};

watch(() => [document.value?.id, document.value?.text], () => {
  messages.value = [];
  error.value = null;
  input.value = "";
});

watch(() => [messages.value.length, open.value], () => {
  scrollToBottom();
});

const send = async (prompt?: string) => {
  if (!hasDocument.value || busy.value) return;
  const question = (prompt ?? input.value).trim();
  if (!question) return;

  const history = toHistoryPayload(messages.value);
  const userMessage: CompanionMessage = {
    id: makeId(),
    role: "user",
    content: question,
    at: Date.now(),
  };

  messages.value = [...messages.value, userMessage];
  if (!prompt) input.value = "";
  busy.value = true;
  error.value = null;

  try {
    const response = await companionAsk({
      question,
      filePath: document.value?.filePath,
      documentTitle: document.value?.title,
      documentText: document.value?.text,
      topic: document.value?.title,
      history,
    });
    const payload = response?.companion;
    const assistantContent = payload?.answer || "I couldn't generate a response from the provided context.";
    const assistantMessage: CompanionMessage = {
      id: makeId(),
      role: "assistant",
      content: assistantContent,
      at: Date.now(),
      flashcards: payload?.flashcards || [],
      topic: payload?.topic,
    };
    messages.value = [...messages.value, assistantMessage];
  } catch (err: any) {
    error.value = err?.message || "Failed to contact companion";
    messages.value = messages.value.slice(0, -1);
  } finally {
    busy.value = false;
  }
};
</script>
