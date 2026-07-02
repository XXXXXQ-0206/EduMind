<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import { MuiPromptBoxPanel } from "../../mui/MuiPromptBoxPanel";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

type MenuOption = { key: string; label: string };

const props = defineProps<{
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  busy?: boolean;
  responseLengthText?: string;
  showLength?: boolean;
  lengths?: readonly MenuOption[];
  onToggleLength?: () => void;
  onSelectLength?: (key: string, label: string) => void;
  onSelectInclude?: (include: boolean) => void;
  mode?: MuiThemeMode;
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiPromptBoxPanel, {
    value: props.value,
    busy: props.busy,
    responseLengthText: props.responseLengthText,
    showLength: props.showLength,
    lengths: props.lengths,
    mode: props.mode,
    onChange: props.onChange,
    onSend: props.onSend,
    onToggleLength: props.onToggleLength,
    onSelectLength: props.onSelectLength,
    onSelectInclude: props.onSelectInclude,
  });
};

onMounted(render);
watch(
  () => [
    props.value,
    props.busy,
    props.responseLengthText,
    props.showLength,
    props.lengths,
    props.mode,
  ],
  render,
  { deep: true },
);
onBeforeUnmount(() => unmountReactBridge(root));
</script>
