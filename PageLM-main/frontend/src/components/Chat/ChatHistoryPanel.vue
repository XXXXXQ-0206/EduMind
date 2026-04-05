<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" />
          </svg>
        </span>
        历史对话
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors"
        @click="startNewChat"
      >
        新建对话
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="chats.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="chat in chats" :key="chat.id" class="flex items-stretch gap-2 min-w-0">
        <button
          type="button"
          class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors"
          @click="openChat(chat.id)"
          @contextmenu.prevent="openContextMenu($event, chat)"
          :title="chat.title || '未命名对话'"
        >
          <div class="truncate">{{ chat.title || "未命名对话" }}</div>
          <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">{{ formatTime(chat.createdAt) }}</div>
        </button>
        <button
          type="button"
          class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center"
          @click.stop="removeChat(chat.id)"
          aria-label="删除对话"
          :title="'删除对话'"
        >
          <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
          </svg>
        </button>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史对话</div>
    <HistoryContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="closeContextMenu"
      @select="addChatToBag"
    />
  </aside>
</template>

<script setup lang="ts">
import { type Ref, inject, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deleteChat, getChats, type ChatInfo } from "../../lib/api";
import { addLearningBagRecord } from "../../lib/learningBag";
import HistoryContextMenu from "../common/HistoryContextMenu.vue";

const router = useRouter();
const route = useRoute();
const chatRole = inject<Ref<"student" | "teacher">>("chatRole");
const chatBasePath = inject<Ref<string>>("chatBasePath");
const loading = ref(false);
const chats = ref<ChatInfo[]>([]);
const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextTarget = ref<ChatInfo | null>(null);

const role = () => chatRole?.value ?? "student";
const basePath = () => chatBasePath?.value ?? "/chat";

const loadChats = async (search?: string) => {
  loading.value = true;
  try {
    const res = await getChats(
      search && search.trim() ? search.trim() : undefined,
      role()
    );
    chats.value = Array.isArray(res?.chats) ? res.chats : [];
  } catch {
    chats.value = [];
  } finally {
    loading.value = false;
  }
};

const openChat = (id: string) => {
  if (!id) return;
  router.push({ path: basePath(), query: { chatId: id }, state: { chatId: id } });
};

const openContextMenu = (event: MouseEvent, chat: ChatInfo) => {
  contextTarget.value = chat;
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
  };
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
};

const addChatToBag = () => {
  const chat = contextTarget.value;
  if (!chat?.id) return;
  addLearningBagRecord({
    type: "chat",
    refId: chat.id,
    title: chat.title || "未命名对话",
    subtitle: formatTime(chat.createdAt),
    path: basePath(),
    query: { chatId: chat.id },
  });
};

const startNewChat = () => {
  router.push({ path: basePath() });
};

const removeChat = async (id: string) => {
  if (!id) return;
  const ok = window.confirm("确定删除该对话吗？");
  if (!ok) return;
  const prev = chats.value;
  chats.value = prev.filter((item) => item.id !== id);
  try {
    await deleteChat(id);
    if ((route.query.chatId as string) === id) {
      router.push({ path: basePath() });
    }
    await loadChats();
  } catch {
    chats.value = prev;
  }
};

const formatTime = (value?: number) => {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
};

onMounted(loadChats);
watch(() => chatRole?.value, () => loadChats());
</script>