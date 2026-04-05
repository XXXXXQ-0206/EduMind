<template>
  <aside class="left-0 bottom-0 w-screen md:w-fit md:h-screen fixed p-4 z-50 lg:flex">
    <div class="w-64 md:order-2 h-full z-40 rounded-l-none rounded-2xl bg-[color:var(--nav-bg)] border border-l-transparent border-[color:var(--nav-border)] hidden flex-col p-4 space-y-3 overflow-y-auto custom-scroll backdrop-blur-2xl">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1 text-[color:var(--nav-text-muted)]">最近文件</h3>
      <RouterLink
        v-for="chat in chats"
        :key="chat.id"
        :to="role === 'teacher' ? `/teacher/chat?chatId=${encodeURIComponent(chat.id)}` : `/chat?chatId=${encodeURIComponent(chat.id)}`"
        class="p-2 hover:text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)] w-full rounded-xl block text-[13px] min-h-fit truncate transition-all duration-200 border border-transparent hover:border-white/10"
      >
        {{ chat.title || "未命名对话" }}
      </RouterLink>
    </div>

    <div class="md:w-56 md:order-1 h-full rounded-3xl bg-[color:var(--nav-bg)] backdrop-blur-2xl border border-[color:var(--nav-border)] text-[color:var(--nav-text-muted)] flex flex-col items-stretch justify-between py-4 shadow-[0_24px_60px_rgba(2,8,23,0.22)]">
      <div class="hidden md:block px-3 text-[18px] font-black tracking-[0.06em] text-[color:var(--nav-text)]">功能</div>
      <nav class="flex md:flex-col items-center space-x-4 md:space-x-0 md:space-y-3 my-auto w-full px-3">
        <RouterLink to="/" :class="navClass('/')" aria-label="项目首页">
          <svg :class="navIconClass('/')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <path d="M9 22V12h6v10" />
          </svg>
          <span class="hidden md:inline text-[14px] whitespace-nowrap">项目首页</span>
        </RouterLink>
        <RouterLink :to="role === 'teacher' ? '/teacher/chat' : '/chat'" :class="navClass(role === 'teacher' ? '/teacher/chat' : '/chat')">
          <svg :class="navIconClass(role === 'teacher' ? '/teacher/chat' : '/chat')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" />
          </svg>
          <span class="hidden md:inline text-[14px] whitespace-nowrap">对话</span>
        </RouterLink>

        <RouterLink :to="role === 'teacher' ? '/teacher/file-library' : '/file-library'" :class="navClass(role === 'teacher' ? '/teacher/file-library' : '/file-library')">
          <svg :class="navIconClass(role === 'teacher' ? '/teacher/file-library' : '/file-library')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 6.5a2.5 2.5 0 0 1 2.5-2.5h3l2 2h6.5A2.5 2.5 0 0 1 20.5 8.5v8A2.5 2.5 0 0 1 18 19H6.5A2.5 2.5 0 0 1 4 16.5v-10Z" />
            <path d="M4 9.5h16.5" />
          </svg>
          <span class="hidden md:inline text-[14px] whitespace-nowrap">文件库</span>
        </RouterLink>

        <template v-if="role === 'teacher'">
          <RouterLink to="/lesson-plan" :class="navClass('/lesson-plan')">
            <svg :class="navIconClass('/lesson-plan')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 3.5h7l3.5 3.5V18a2.5 2.5 0 0 1-2.5 2.5H7A2.5 2.5 0 0 1 4.5 18V6A2.5 2.5 0 0 1 7 3.5Z" />
              <path d="M14 3.5V7h3.5" />
              <path d="m8.5 12 2 2 4-4" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">教案</span>
          </RouterLink>
          <RouterLink to="/slides" :class="navClass('/slides')">
            <svg :class="navIconClass('/slides')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" />
              <path d="M8 19.5h8" />
              <path d="M10 16.5v3" />
              <path d="M14 16.5v3" />
              <path d="m7 11 2.5-2.5 2.5 2.5 3-3 2 2" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">教学幻灯片</span>
          </RouterLink>
          <RouterLink to="/teaching-video" :class="navClass('/teaching-video')">
            <svg :class="navIconClass('/teaching-video')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 6.5A2.5 2.5 0 0 1 7.5 4h6A2.5 2.5 0 0 1 16 6.5v11A2.5 2.5 0 0 1 13.5 20h-6A2.5 2.5 0 0 1 5 17.5v-11Z" />
              <path d="m16 10 4-2.5v9L16 14" />
              <path d="m9.5 9 3 2-3 2v-4Z" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">教学视频</span>
          </RouterLink>
          <RouterLink to="/teacher/bili-learning" :class="navClass('/teacher/bili-learning')">
            <svg :class="navIconClass('/teacher/bili-learning')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5.5 6.5A2.5 2.5 0 0 1 8 4h8a2.5 2.5 0 0 1 2.5 2.5v11A2.5 2.5 0 0 1 16 20H8a2.5 2.5 0 0 1-2.5-2.5v-11Z" />
              <path d="m10 9 5 3-5 3V9Z" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">bilibili视频备课</span>
          </RouterLink>
          <RouterLink to="/teacher/quiz" :class="navClass('/teacher/quiz')">
            <svg :class="navIconClass('/teacher/quiz')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3.5a6.5 6.5 0 0 0-3.5 11.98V17.5h7v-2.02A6.5 6.5 0 0 0 12 3.5Z" />
              <path d="M9.5 20.5h5" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">测验</span>
          </RouterLink>
          <RouterLink to="/teacher/paper" :class="navClass('/teacher/paper')">
            <svg :class="navIconClass('/teacher/paper')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">试卷</span>
          </RouterLink>
          <RouterLink to="/teaching-records" :class="navClass('/teaching-records')">
            <svg :class="navIconClass('/teaching-records')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4.5 6.5h15" />
              <path d="M4.5 12h15" />
              <path d="M4.5 17.5h10.5" />
              <path d="M17 16.5 19.5 19l2-2" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">教学记录汇</span>
          </RouterLink>
        </template>

        <template v-else>
          <RouterLink to="/smart-notes" :class="navClass('/smart-notes')">
            <svg :class="navIconClass('/smart-notes')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 3.5h7l3.5 3.5V18a2.5 2.5 0 0 1-2.5 2.5H7A2.5 2.5 0 0 1 4.5 18V6A2.5 2.5 0 0 1 7 3.5Z" />
              <path d="M14 3.5V7h3.5" />
              <path d="M9 12h6" />
              <path d="M9 15.5h4" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">智能笔记</span>
          </RouterLink>
          <RouterLink to="/podcast" :class="navClass('/podcast')">
            <svg :class="navIconClass('/podcast')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 4a6 6 0 0 0-6 6v2a6 6 0 0 0 12 0v-2a6 6 0 0 0-6-6Z" />
              <path d="M9.5 19.5h5" />
              <path d="M10.5 15.5h3" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">AI播客</span>
          </RouterLink>
          <RouterLink to="/quiz" :class="navClass('/quiz')">
            <svg :class="navIconClass('/quiz')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3.5a6.5 6.5 0 0 0-3.5 11.98V17.5h7v-2.02A6.5 6.5 0 0 0 12 3.5Z" />
              <path d="M9.5 20.5h5" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">测验</span>
          </RouterLink>
          <RouterLink to="/knowledge-cards" :class="navClass('/knowledge-cards')">
            <svg :class="navIconClass('/knowledge-cards')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 4.5h10A2.5 2.5 0 0 1 19.5 7v10A2.5 2.5 0 0 1 17 19.5H7A2.5 2.5 0 0 1 4.5 17V7A2.5 2.5 0 0 1 7 4.5Z" />
              <path d="M8.5 8.5h7" />
              <path d="M8.5 12h4.5" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">知识卡片</span>
          </RouterLink>
          <RouterLink to="/bili-learning" :class="navClass('/bili-learning')">
            <svg :class="navIconClass('/bili-learning')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5.5 6.5A2.5 2.5 0 0 1 8 4h8a2.5 2.5 0 0 1 2.5 2.5v11A2.5 2.5 0 0 1 16 20H8a2.5 2.5 0 0 1-2.5-2.5v-11Z" />
              <path d="m10 9 5 3-5 3V9Z" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">bilibili视频学习</span>
          </RouterLink>
          <RouterLink to="/wrong-book" :class="navClass('/wrong-book')">
            <svg :class="navIconClass('/wrong-book')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 5.5h10.5A2.5 2.5 0 0 1 19 8v9.5A2.5 2.5 0 0 1 16.5 20H6A2.5 2.5 0 0 1 3.5 17.5V8A2.5 2.5 0 0 1 6 5.5Z" />
              <path d="M8.5 9.5h6" />
              <path d="M8.5 13.5h4" />
              <path d="M17.5 7.5 20.5 5" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">错题本</span>
          </RouterLink>
          <RouterLink to="/learning-records" :class="navClass('/learning-records')">
            <svg :class="navIconClass('/learning-records')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4.5 6.5h15" />
              <path d="M4.5 12h15" />
              <path d="M4.5 17.5h10.5" />
              <path d="M17 16.5 19.5 19l2-2" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">学习记录汇</span>
          </RouterLink>
          <RouterLink to="/english-speaking" :class="navClass('/english-speaking')">
            <svg :class="navIconClass('/english-speaking')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 4a6.5 6.5 0 1 0 3.5 12.02L18 20l-6-1.5A6.5 6.5 0 0 1 12 4Z" />
              <path d="M9.5 9.5h5" />
              <path d="M9.5 12.5h3" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">英语口语</span>
          </RouterLink>
          <RouterLink to="/cards" :class="navClass('/cards')">
            <svg :class="navIconClass('/cards')" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 5.5h12A2.5 2.5 0 0 1 20.5 8v7.5A3 3 0 0 1 17.5 18.5H6A2.5 2.5 0 0 1 3.5 16V8A2.5 2.5 0 0 1 6 5.5Z" />
              <path d="M9.5 10.5h5" />
              <path d="M12 8v6" />
            </svg>
            <span class="hidden md:inline text-[14px] whitespace-nowrap">学习袋</span>
          </RouterLink>
        </template>

        <button
          type="button"
          :class="navActionClass"
          aria-label="账户设置"
          @click="handleAccountAction"
        >
          <svg class="size-[20px] flex-shrink-0 text-[color:var(--nav-text-muted)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.325 4.317a1.724 1.724 0 0 1 3.35 0 1.724 1.724 0 0 0 2.573 1.066 1.724 1.724 0 0 1 2.302.989 1.724 1.724 0 0 0 2.02 1.442 1.724 1.724 0 0 1 1.441 2.02 1.724 1.724 0 0 0 .99 2.302 1.724 1.724 0 0 1 0 3.35 1.724 1.724 0 0 0-.99 2.573 1.724 1.724 0 0 1-.989 2.302 1.724 1.724 0 0 0-1.442 2.02 1.724 1.724 0 0 1-2.02 1.441 1.724 1.724 0 0 0-2.302.99 1.724 1.724 0 0 1-3.35 0 1.724 1.724 0 0 0-2.573-1.066 1.724 1.724 0 0 1-2.302-.989 1.724 1.724 0 0 0-2.02-1.442 1.724 1.724 0 0 1-1.441-2.02 1.724 1.724 0 0 0-.99-2.302 1.724 1.724 0 0 1 0-3.35 1.724 1.724 0 0 0 .99-2.573 1.724 1.724 0 0 1 .989-2.302 1.724 1.724 0 0 0 1.442-2.02 1.724 1.724 0 0 1 2.02-1.441 1.724 1.724 0 0 0 2.302-.99Z" />
            <path d="M12 15.75A3.75 3.75 0 1 0 12 8.25a3.75 3.75 0 0 0 0 7.5Z" />
          </svg>
          <span class="hidden md:inline text-[14px] whitespace-nowrap">设置</span>
        </button>
      </nav>

      <div class="hidden md:block px-3 pt-3">
        <div class="rounded-[26px] border border-[color:var(--sidebar-card-border)] bg-[color:var(--sidebar-card-bg)] px-4 py-4 shadow-[0_12px_28px_rgba(2,8,23,0.14)]">
          <div class="text-[11px] uppercase tracking-[0.18em] text-[color:var(--nav-text-muted)]">账户</div>
          <div class="mt-3 text-lg font-extrabold text-[color:var(--nav-text)] truncate">{{ username || "未登录" }}</div>
          <div v-if="isAuthenticated" class="mt-4 grid gap-2">
            <button
              type="button"
              class="w-full rounded-2xl border border-[color:var(--sidebar-card-border)] bg-[color:var(--sidebar-button-bg)] px-3 py-2.5 text-sm font-semibold text-[color:var(--nav-text)] transition hover:bg-[color:var(--sidebar-button-hover)] cursor-pointer"
              @click="showSettings = true"
            >
              账户设置
            </button>
            <button
              type="button"
              class="w-full rounded-2xl border border-[color:var(--sidebar-card-border)] bg-[color:var(--sidebar-button-bg)] px-3 py-2.5 text-sm font-semibold text-[color:var(--nav-text)] transition hover:bg-[color:var(--sidebar-button-hover)] cursor-pointer"
              @click="handleLogout"
            >
              退出登录
            </button>
          </div>
          <div v-else class="mt-4 grid gap-2">
            <button
              type="button"
              class="w-full rounded-2xl border border-[color:var(--sidebar-card-border)] bg-[color:var(--sidebar-button-bg)] px-3 py-2.5 text-sm font-semibold text-[color:var(--nav-text)] transition hover:bg-[color:var(--sidebar-button-hover)] cursor-pointer"
              @click="goToAuth"
            >
              登录 / 注册
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>

  <AccountSettingsModal
    :open="showSettings"
    :username="username || '当前账户'"
    @close="showSettings = false"
    @session-ended="handleSessionEnded"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AccountSettingsModal from "./AccountSettingsModal.vue";
import { getChats, type ChatsList } from "../lib/api";
import { useAuthStore } from "../stores/auth";
import { useRoleStore } from "../stores/role";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const roleStore = useRoleStore();
const chats = ref<ChatsList["chats"]>([]);
const showSettings = ref(false);

const role = computed(() => roleStore.role);
const username = computed(() => authStore.username);
const isAuthenticated = computed(() => authStore.isAuthenticated);

const loadChats = async () => {
  if (!isAuthenticated.value) {
    chats.value = [];
    return;
  }
  try {
    const roleParam = role.value === "teacher" ? "teacher" : "student";
    const data = await getChats(undefined, roleParam);
    chats.value = data.chats || [];
  } catch {
    chats.value = [];
  }
};

const navClass = (path: string) =>
  `w-full px-3 py-2.5 min-h-[40px] rounded-xl duration-300 transition-all flex items-center justify-start gap-3 text-[14px] cursor-pointer border border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring-color)] ${
    route.path === path
      ? "text-[color:var(--nav-active-text)] bg-[color:var(--nav-active-bg)] border-[color:var(--nav-active-border)] shadow-[var(--nav-active-shadow)]"
      : "text-[color:var(--nav-text-muted)] hover:text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]"
  }`;

const navIconClass = (path: string) =>
  `size-[20px] flex-shrink-0 ${
    route.path === path
      ? "text-[color:var(--nav-active-icon)] drop-shadow-[var(--nav-icon-glow)]"
      : "text-[color:var(--nav-text-muted)] drop-shadow-[var(--nav-icon-muted-glow)]"
  }`;

const navActionClass =
  "w-full px-3 py-2.5 min-h-[40px] rounded-xl duration-300 transition-all flex items-center justify-start gap-3 text-[14px] cursor-pointer border border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring-color)] text-[color:var(--nav-text-muted)] hover:text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg)]";


onMounted(async () => {
  await authStore.hydrate();
  await loadChats();
});
watch([role, isAuthenticated], loadChats);

const goToAuth = async () => {
  await router.push({
    path: "/auth",
    query: { role: role.value },
  });
};

const handleAccountAction = async () => {
  if (!isAuthenticated.value) {
    await goToAuth();
    return;
  }
  showSettings.value = true;
};

const handleLogout = async () => {
  if (!isAuthenticated.value) {
    await goToAuth();
    return;
  }
  await authStore.logout();
  chats.value = [];
  await router.push({ path: "/auth", query: { role: role.value } });
};

const handleSessionEnded = async (reason: "password-changed" | "account-deleted") => {
  showSettings.value = false;
  chats.value = [];
  await router.push({
    path: "/auth",
    query: {
      role: role.value,
      reason,
    },
  });
};
</script>
