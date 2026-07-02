<template>
  <!-- 替换：原自定义 PromptBox/textarea/菜单/发送按钮 → MUI Paper/TextField/Menu/IconButton，功能已保留 -->
  <MuiPromptBoxAdapter
    :value="value"
    :on-change="onChange"
    :on-send="onSend"
    :busy="busy"
    :response-length-text="responseLengthText"
    :show-length="showLength"
    :lengths="lengths"
    :on-toggle-length="onToggleLength"
    :on-select-length="onSelectLength"
    :on-select-include="onSelectInclude"
    :mode="theme.mode"
  />
</template>

<script setup lang="ts">
import MuiPromptBoxAdapter from "../mui/MuiPromptBoxAdapter.vue";
import { useThemeStore } from "../../stores/theme";

type MenuOption = { key: string; label: string };

defineProps<{
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  busy?: boolean;
  responseLengthText?: string;
  showLength?: boolean;
  lengths?: readonly MenuOption[];
  onToggleLength?: () => void;
  onSelectLength?: (key: string, label: string) => void;
  onSelectInclude?: (include: boolean) => void;
}>();

const theme = useThemeStore();
</script>
