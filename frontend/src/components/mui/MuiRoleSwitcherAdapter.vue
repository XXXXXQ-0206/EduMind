<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import { MuiRoleSwitcherPanel, type MuiUserRole } from "../../mui/MuiRoleSwitcherPanel";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

const props = defineProps<{
  role: MuiUserRole;
  mode?: MuiThemeMode;
}>();

const emit = defineEmits<{
  "role-change": [role: MuiUserRole];
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiRoleSwitcherPanel, {
    role: props.role,
    mode: props.mode,
    onRoleChange: (role) => emit("role-change", role),
  });
};

onMounted(render);
watch(() => [props.role, props.mode], render);
onBeforeUnmount(() => unmountReactBridge(root));
</script>
