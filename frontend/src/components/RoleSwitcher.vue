<template>
  <!-- 替换：原自定义角色切换器 → MUI ToggleButtonGroup，功能已保留 -->
  <MuiRoleSwitcherAdapter :role="role" :mode="theme.mode" @role-change="setRole" />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import MuiRoleSwitcherAdapter from "./mui/MuiRoleSwitcherAdapter.vue";
import { useRoleStore } from "../stores/role";
import { useThemeStore } from "../stores/theme";

const router = useRouter();
const roleStore = useRoleStore();
const theme = useThemeStore();
const role = computed(() => roleStore.role);

const setRole = (next: "teacher" | "student") => {
  roleStore.setRole(next);
  router.push(next === "teacher" ? "/teacher/chat" : "/chat");
};
</script>
