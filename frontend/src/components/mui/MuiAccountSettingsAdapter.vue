<template>
  <div ref="hostRef"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { Root } from "react-dom/client";
import { MuiAccountSettingsDialog } from "../../mui/MuiAccountSettingsDialog";
import { renderReactBridge, unmountReactBridge } from "../../mui/reactBridge";
import type { MuiThemeMode } from "../../mui/MuiSurface";

const props = defineProps<{
  open: boolean;
  username: string;
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
  deletePassword: string;
  showOldPassword: boolean;
  showNewPassword: boolean;
  showConfirmPassword: boolean;
  showDeletePassword: boolean;
  passwordError?: string;
  deleteError?: string;
  passwordSubmitting?: boolean;
  deleteSubmitting?: boolean;
  confirmingDeletion?: boolean;
  mode?: MuiThemeMode;
}>();

const emit = defineEmits<{
  close: [];
  "update-old-password": [value: string];
  "update-new-password": [value: string];
  "update-confirm-password": [value: string];
  "update-delete-password": [value: string];
  "toggle-old-password": [];
  "toggle-new-password": [];
  "toggle-confirm-password": [];
  "toggle-delete-password": [];
  "submit-password": [];
  "open-delete-confirm": [];
  "close-delete-confirm": [];
  "submit-delete-account": [];
}>();

const hostRef = ref<HTMLElement | null>(null);
let root: Root | null = null;

const render = () => {
  root = renderReactBridge(hostRef.value, root, MuiAccountSettingsDialog, {
    open: props.open,
    username: props.username,
    oldPassword: props.oldPassword,
    newPassword: props.newPassword,
    confirmPassword: props.confirmPassword,
    deletePassword: props.deletePassword,
    showOldPassword: props.showOldPassword,
    showNewPassword: props.showNewPassword,
    showConfirmPassword: props.showConfirmPassword,
    showDeletePassword: props.showDeletePassword,
    passwordError: props.passwordError,
    deleteError: props.deleteError,
    passwordSubmitting: props.passwordSubmitting,
    deleteSubmitting: props.deleteSubmitting,
    confirmingDeletion: props.confirmingDeletion,
    mode: props.mode,
    onClose: () => emit("close"),
    onOldPasswordChange: (value) => emit("update-old-password", value),
    onNewPasswordChange: (value) => emit("update-new-password", value),
    onConfirmPasswordChange: (value) => emit("update-confirm-password", value),
    onDeletePasswordChange: (value) => emit("update-delete-password", value),
    onToggleOldPassword: () => emit("toggle-old-password"),
    onToggleNewPassword: () => emit("toggle-new-password"),
    onToggleConfirmPassword: () => emit("toggle-confirm-password"),
    onToggleDeletePassword: () => emit("toggle-delete-password"),
    onSubmitPasswordChange: () => emit("submit-password"),
    onOpenDeleteConfirm: () => emit("open-delete-confirm"),
    onCloseDeleteConfirm: () => emit("close-delete-confirm"),
    onSubmitDeleteAccount: () => emit("submit-delete-account"),
  });
};

onMounted(render);
watch(
  () => [
    props.open,
    props.username,
    props.oldPassword,
    props.newPassword,
    props.confirmPassword,
    props.deletePassword,
    props.showOldPassword,
    props.showNewPassword,
    props.showConfirmPassword,
    props.showDeletePassword,
    props.passwordError,
    props.deleteError,
    props.passwordSubmitting,
    props.deleteSubmitting,
    props.confirmingDeletion,
    props.mode,
  ],
  render,
);
onBeforeUnmount(() => unmountReactBridge(root));
</script>
