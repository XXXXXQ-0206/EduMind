<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import {
  MuiSidebarShell,
  type MuiSidebarChat,
  type MuiSidebarRole,
} from "../../mui/MuiSidebarShell";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

const props = defineProps<{
  activePath: string;
  role: MuiSidebarRole;
  username?: string;
  isAuthenticated: boolean;
  chats: MuiSidebarChat[];
  mode?: MuiThemeMode;
}>();

const emit = defineEmits<{
  navigate: [path: string];
  "account-action": [];
  logout: [];
  auth: [];
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiSidebarShell, {
    activePath: props.activePath,
    role: props.role,
    username: props.username,
    isAuthenticated: props.isAuthenticated,
    chats: props.chats,
    mode: props.mode,
    onNavigate: (path) => emit("navigate", path),
    onAccountAction: () => emit("account-action"),
    onLogout: () => emit("logout"),
    onAuth: () => emit("auth"),
  });
};

onMounted(render);
watch(
  () => [
    props.activePath,
    props.role,
    props.username,
    props.isAuthenticated,
    props.chats,
    props.mode,
  ],
  render,
  { deep: true },
);
onBeforeUnmount(() => unmountReactBridge(root));
</script>
