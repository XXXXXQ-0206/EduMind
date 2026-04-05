<template>
  <div class="fixed top-16 left-4 right-4 md:left-auto md:right-4 z-50 flex items-center justify-center md:justify-end">
    <div class="relative w-full max-w-[220px] rounded-full bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] shadow-[0_12px_26px_rgba(15,23,42,0.12),0_1px_0_rgba(255,255,255,0.25)] backdrop-blur px-1 py-1 flex items-center">
      <span class="absolute -top-2 -left-2 text-[color:var(--tone-sky-text)]/70">
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5l1.5 3.5 3.5 1.5-3.5 1.5L12 15l-1.5-3.5-3.5-1.5 3.5-1.5L12 4.5Z" />
        </svg>
      </span>
      <span
        class="absolute top-1 bottom-1 left-1 w-1/2 rounded-full bg-gradient-to-r from-[color:var(--role-pill-from)] to-[color:var(--role-pill-to)] shadow-[var(--role-pill-shadow)] transition-transform duration-300"
        :class="role === 'teacher' ? 'translate-x-0' : 'translate-x-full'"
        style="transition-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1);"
      ></span>
      <button
        type="button"
        class="relative z-10 flex-1 px-3 py-2 text-xs font-semibold text-[color:var(--app-text)] rounded-full transition-colors"
        :class="role === 'teacher' ? 'text-[color:var(--role-active-text)]' : 'text-[color:var(--nav-text-muted)]'"
        @click="setRole('teacher')"
      >
        教师
      </button>
      <button
        type="button"
        class="relative z-10 flex-1 px-3 py-2 text-xs font-semibold text-[color:var(--app-text)] rounded-full transition-colors"
        :class="role === 'student' ? 'text-[color:var(--role-active-text)]' : 'text-[color:var(--nav-text-muted)]'"
        @click="setRole('student')"
      >
        学生
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useRoleStore } from "../stores/role";

const router = useRouter();
const roleStore = useRoleStore();
const role = computed(() => roleStore.role);

const setRole = (next: "teacher" | "student") => {
  roleStore.setRole(next);
  router.push(next === "teacher" ? "/teacher/chat" : "/chat");
};
</script>
