<template>
  <div>
    <div class="ambient-glow ambient-glow-cyan"></div>
    <div class="ambient-glow ambient-glow-orange"></div>

    <div class="min-h-screen flex flex-col relative z-10 text-[color:var(--app-text)]">
      <Sidebar v-if="!route.meta?.hideSidebar" />
      <div class="flex-1 relative overflow-hidden min-h-0 flex flex-col">
        <Transition :name="route.meta?.hideSidebar ? 'intro-slide' : 'fade'" mode="out-in">
          <div :key="route.fullPath" class="min-h-full w-full flex flex-col">
            <RouterView />
          </div>
        </Transition>
      </div>
    </div>

    <RoleSwitcher v-if="!route.meta?.hideSidebar" />
    <ThemeToggle />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
import { RouterView, useRoute } from "vue-router";
import Sidebar from "./components/Sidebar.vue";
import RoleSwitcher from "./components/RoleSwitcher.vue";
import ThemeToggle from "./components/ThemeToggle.vue";
import { useAuthStore } from "./stores/auth";
import { useThemeStore } from "./stores/theme";
import { useRoleStore } from "./stores/role";

const route = useRoute();
const authStore = useAuthStore();
const theme = useThemeStore();
const roleStore = useRoleStore();

onMounted(() => {
  theme.init();
  authStore.hydrate();
});

watch(
  () => roleStore.role,
  (role) => {
    document.documentElement.classList.toggle("role-teacher", role === "teacher");
    document.documentElement.classList.toggle("role-student", role === "student");
  },
  { immediate: true }
);
</script>

<style>
/* 介绍页 / 首页：全屏水平推移，体现 Link 顺滑感 */
.intro-slide-enter-active,
.intro-slide-leave-active {
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.35s ease;
}

.intro-slide-enter-from {
  transform: translateX(100%);
  opacity: 0.85;
}

.intro-slide-enter-to {
  transform: translateX(0);
  opacity: 1;
}

.intro-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}

.intro-slide-leave-to {
  transform: translateX(-28%);
  opacity: 0.9;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
