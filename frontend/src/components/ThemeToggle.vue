<template>
  <!-- 替换：原自定义主题切换按钮 → MUI Fab，功能已保留 -->
  <MuiThemeToggleAdapter :mode="theme.mode" @toggle="theme.toggle" />
</template>

<script setup lang="ts">
import MuiThemeToggleAdapter from "./mui/MuiThemeToggleAdapter.vue";
import { useThemeStore } from "../stores/theme";

const theme = useThemeStore();
</script>
