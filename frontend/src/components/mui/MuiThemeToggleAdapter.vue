<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import { MuiThemeToggleButton } from "../../mui/MuiThemeToggleButton";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

const props = defineProps<{
  mode: MuiThemeMode;
}>();

const emit = defineEmits<{
  toggle: [];
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiThemeToggleButton, {
    mode: props.mode,
    onToggle: () => emit("toggle"),
  });
};

onMounted(render);
watch(() => props.mode, render);
onBeforeUnmount(() => unmountReactBridge(root));
</script>
