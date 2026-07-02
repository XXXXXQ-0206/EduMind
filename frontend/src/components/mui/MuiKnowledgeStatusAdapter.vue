<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import { MuiKnowledgeStatusPanel } from "../../mui/MuiKnowledgeStatusPanel";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

type KnowledgeStatus = "mastered" | "pending" | "review";

const props = defineProps<{
  counts: Record<KnowledgeStatus, number>;
  loading?: boolean;
  mode?: MuiThemeMode;
}>();

const emit = defineEmits<{
  refresh: [];
  "status-click": [status: KnowledgeStatus];
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiKnowledgeStatusPanel, {
    counts: props.counts,
    loading: props.loading,
    mode: props.mode,
    onRefresh: () => emit("refresh"),
    onStatusClick: (status) => emit("status-click", status),
  });
};

onMounted(render);
watch(() => [props.counts, props.loading, props.mode], render, { deep: true });
onBeforeUnmount(() => unmountReactBridge(root));
</script>
