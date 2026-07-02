<template>
  <!-- 替换：原自定义账户设置 Modal/确认弹窗/表单控件 → MUI Dialog/TextField/Button/Alert，功能已保留 -->
  <MuiAccountSettingsAdapter
    :open="open"
    :username="username"
    :old-password="oldPassword"
    :new-password="newPassword"
    :confirm-password="confirmPassword"
    :delete-password="deletePassword"
    :show-old-password="showOldPassword"
    :show-new-password="showNewPassword"
    :show-confirm-password="showConfirmPassword"
    :show-delete-password="showDeletePassword"
    :password-error="passwordError"
    :delete-error="deleteError"
    :password-submitting="passwordSubmitting"
    :delete-submitting="deleteSubmitting"
    :confirming-deletion="confirmingDeletion"
    :mode="themeStore.mode"
    @close="closeModal"
    @update-old-password="setOldPassword"
    @update-new-password="setNewPassword"
    @update-confirm-password="setConfirmPassword"
    @update-delete-password="setDeletePassword"
    @toggle-old-password="toggleOldPassword"
    @toggle-new-password="toggleNewPassword"
    @toggle-confirm-password="toggleConfirmPassword"
    @toggle-delete-password="toggleDeletePassword"
    @submit-password="submitPasswordChange"
    @open-delete-confirm="openDeleteConfirm"
    @close-delete-confirm="closeDeleteConfirm"
    @submit-delete-account="submitDeleteAccount"
  />

  <Teleport v-if="legacyAccountSettingsVisible" to="body">
    <div v-if="open" class="fixed inset-0 z-[80] flex items-center justify-center p-4">
      <button
        type="button"
        class="absolute inset-0 bg-slate-950/45 backdrop-blur-[3px] cursor-pointer"
        aria-label="关闭设置"
        @click="closeModal"
      ></button>

      <div class="relative z-[81] max-h-[min(88vh,760px)] w-full max-w-2xl overflow-y-auto rounded-[28px] border border-white/55 bg-[color:var(--glass-bg)] p-5 shadow-[0_30px_80px_rgba(15,23,42,0.24)] backdrop-blur-2xl custom-scroll md:p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[color:var(--nav-text-muted)]">Account Settings</div>
            <h2 class="mt-2 text-2xl font-black tracking-tight text-[color:var(--app-text)]">账户设置</h2>
            <p class="mt-2 text-sm leading-6 text-[color:var(--nav-text-muted)]">
              当前账户：<span class="font-semibold text-[color:var(--app-text)]">{{ username }}</span>
            </p>
          </div>
          <button
            type="button"
            class="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-[color:var(--nav-border)] bg-white/20 text-[color:var(--nav-text)] transition hover:bg-white/35 cursor-pointer"
            aria-label="关闭设置"
            @click="closeModal"
          >
            <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </div>

        <div class="mt-6 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <section class="rounded-[24px] border border-[color:var(--nav-border)] bg-white/20 p-5">
            <div class="flex items-center gap-3">
              <div class="flex size-10 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-500">
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V7.875A4.875 4.875 0 0 0 6.75 7.875V10.5m-1.5 0h12.75A1.5 1.5 0 0 1 19.5 12v7.5A1.5 1.5 0 0 1 18 21H6a1.5 1.5 0 0 1-1.5-1.5V12a1.5 1.5 0 0 1 1.5-1.5Z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-bold text-[color:var(--app-text)]">修改密码</h3>
                <p class="mt-1 text-sm text-[color:var(--nav-text-muted)]">修改成功后将退出当前登录，需要重新登录。</p>
              </div>
            </div>

            <form class="mt-5 space-y-4" @submit.prevent="submitPasswordChange">
              <label class="block">
                <span class="mb-2 block text-sm font-semibold text-[color:var(--app-text)]">旧密码</span>
                <div class="settings-input-wrap">
                  <input v-model="oldPassword" :type="showOldPassword ? 'text' : 'password'" autocomplete="current-password" class="settings-input settings-input-with-toggle" />
                  <button
                    type="button"
                    class="settings-visibility-btn"
                    :aria-label="showOldPassword ? '隐藏旧密码' : '显示旧密码'"
                    @click="showOldPassword = !showOldPassword"
                  >
                    <svg v-if="showOldPassword" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 3 21 21" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.58 10.58a2 2 0 0 0 2.84 2.84" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.88 4.24A9.76 9.76 0 0 1 12 4.5c4.64 0 8.58 3.02 9.96 7.18a1 1 0 0 1 0 .64 10.49 10.49 0 0 1-4.29 5.27M6.23 6.23A10.54 10.54 0 0 0 2.04 11.68a1 1 0 0 0 0 .64C3.42 16.48 7.36 19.5 12 19.5c1.54 0 3-.33 4.31-.92" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.04 12.32C3.42 8.15 7.36 5.13 12 5.13s8.58 3.02 9.96 7.19a1 1 0 0 1 0 .63C20.58 17.11 16.64 20.13 12 20.13S3.42 17.11 2.04 12.95a1 1 0 0 1 0-.63Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12.63a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  </button>
                </div>
              </label>
              <label class="block">
                <span class="mb-2 block text-sm font-semibold text-[color:var(--app-text)]">新密码</span>
                <div class="settings-input-wrap">
                  <input v-model="newPassword" :type="showNewPassword ? 'text' : 'password'" autocomplete="new-password" class="settings-input settings-input-with-toggle" />
                  <button
                    type="button"
                    class="settings-visibility-btn"
                    :aria-label="showNewPassword ? '隐藏新密码' : '显示新密码'"
                    @click="showNewPassword = !showNewPassword"
                  >
                    <svg v-if="showNewPassword" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 3 21 21" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.58 10.58a2 2 0 0 0 2.84 2.84" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.88 4.24A9.76 9.76 0 0 1 12 4.5c4.64 0 8.58 3.02 9.96 7.18a1 1 0 0 1 0 .64 10.49 10.49 0 0 1-4.29 5.27M6.23 6.23A10.54 10.54 0 0 0 2.04 11.68a1 1 0 0 0 0 .64C3.42 16.48 7.36 19.5 12 19.5c1.54 0 3-.33 4.31-.92" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.04 12.32C3.42 8.15 7.36 5.13 12 5.13s8.58 3.02 9.96 7.19a1 1 0 0 1 0 .63C20.58 17.11 16.64 20.13 12 20.13S3.42 17.11 2.04 12.95a1 1 0 0 1 0-.63Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12.63a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  </button>
                </div>
              </label>
              <label class="block">
                <span class="mb-2 block text-sm font-semibold text-[color:var(--app-text)]">确认新密码</span>
                <div class="settings-input-wrap">
                  <input v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" autocomplete="new-password" class="settings-input settings-input-with-toggle" />
                  <button
                    type="button"
                    class="settings-visibility-btn"
                    :aria-label="showConfirmPassword ? '隐藏确认密码' : '显示确认密码'"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <svg v-if="showConfirmPassword" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 3 21 21" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.58 10.58a2 2 0 0 0 2.84 2.84" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.88 4.24A9.76 9.76 0 0 1 12 4.5c4.64 0 8.58 3.02 9.96 7.18a1 1 0 0 1 0 .64 10.49 10.49 0 0 1-4.29 5.27M6.23 6.23A10.54 10.54 0 0 0 2.04 11.68a1 1 0 0 0 0 .64C3.42 16.48 7.36 19.5 12 19.5c1.54 0 3-.33 4.31-.92" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.04 12.32C3.42 8.15 7.36 5.13 12 5.13s8.58 3.02 9.96 7.19a1 1 0 0 1 0 .63C20.58 17.11 16.64 20.13 12 20.13S3.42 17.11 2.04 12.95a1 1 0 0 1 0-.63Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12.63a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  </button>
                </div>
              </label>

              <p v-if="passwordError" class="rounded-2xl border border-rose-300/60 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                {{ passwordError }}
              </p>

              <button type="submit" class="settings-primary-btn" :disabled="passwordSubmitting">
                {{ passwordSubmitting ? "提交中..." : "保存新密码" }}
              </button>
            </form>
          </section>

          <section class="rounded-[24px] border border-rose-300/30 bg-rose-500/10 p-5">
            <div class="flex items-center gap-3">
              <div class="flex size-10 items-center justify-center rounded-2xl bg-rose-500/20 text-rose-300">
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 7.5h12m-1.5 0-.75 11.25A1.5 1.5 0 0 1 14.255 20H9.745a1.5 1.5 0 0 1-1.495-1.25L7.5 7.5m3-3h3a1.5 1.5 0 0 1 1.5 1.5v1.5h-6V6a1.5 1.5 0 0 1 1.5-1.5Z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-bold text-[color:var(--app-text)]">注销账户</h3>
                <p class="mt-1 text-sm text-[color:var(--nav-text-muted)]">只会注销当前正在使用的账户，删除后不可恢复。</p>
              </div>
            </div>

            <div class="mt-5">
              <label class="block">
                <span class="mb-2 block text-sm font-semibold text-[color:var(--app-text)]">账户密码</span>
                <div class="settings-input-wrap">
                  <input v-model="deletePassword" :type="showDeletePassword ? 'text' : 'password'" autocomplete="current-password" class="settings-input settings-input-danger settings-input-with-toggle" />
                  <button
                    type="button"
                    class="settings-visibility-btn settings-visibility-btn-danger"
                    :aria-label="showDeletePassword ? '隐藏账户密码' : '显示账户密码'"
                    @click="showDeletePassword = !showDeletePassword"
                  >
                    <svg v-if="showDeletePassword" viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 3 21 21" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.58 10.58a2 2 0 0 0 2.84 2.84" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.88 4.24A9.76 9.76 0 0 1 12 4.5c4.64 0 8.58 3.02 9.96 7.18a1 1 0 0 1 0 .64 10.49 10.49 0 0 1-4.29 5.27M6.23 6.23A10.54 10.54 0 0 0 2.04 11.68a1 1 0 0 0 0 .64C3.42 16.48 7.36 19.5 12 19.5c1.54 0 3-.33 4.31-.92" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.04 12.32C3.42 8.15 7.36 5.13 12 5.13s8.58 3.02 9.96 7.19a1 1 0 0 1 0 .63C20.58 17.11 16.64 20.13 12 20.13S3.42 17.11 2.04 12.95a1 1 0 0 1 0-.63Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12.63a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  </button>
                </div>
              </label>
            </div>

            <p v-if="deleteError" class="mt-4 rounded-2xl border border-rose-300/60 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {{ deleteError }}
            </p>

            <button
              type="button"
              class="mt-5 inline-flex min-h-[48px] w-full items-center justify-center rounded-2xl border border-rose-300/45 bg-rose-500/15 px-4 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/20 cursor-pointer"
              @click="openDeleteConfirm"
            >
              注销当前账户
            </button>
          </section>
        </div>
      </div>

      <div v-if="confirmingDeletion" class="fixed inset-0 z-[82] flex items-center justify-center p-4">
        <button
          type="button"
          class="absolute inset-0 bg-slate-950/55 backdrop-blur-[3px] cursor-pointer"
          aria-label="关闭确认"
          @click="closeDeleteConfirm"
        ></button>
        <div class="confirm-dialog relative z-[83] w-full max-w-md rounded-[26px] p-6">
          <div class="flex items-center gap-3">
            <div class="confirm-dialog-icon flex size-11 items-center justify-center rounded-2xl">
              <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4.5m0 3h.008v.008H12V16.5Zm8.25-4.65c0 4.56-3.69 8.25-8.25 8.25S3.75 16.41 3.75 11.85 7.44 3.6 12 3.6s8.25 3.69 8.25 8.25Z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-bold text-[color:var(--app-text)]">确认注销账户</h3>
              <p class="mt-1 text-sm leading-6 text-[color:var(--nav-text-muted)]">该操作会删除当前账户及其对应历史数据，且无法恢复。</p>
            </div>
          </div>

          <div class="confirm-dialog-account mt-6 rounded-2xl px-4 py-3 text-sm text-[color:var(--nav-text)]">
            账户：<span class="font-semibold text-[color:var(--app-text)]">{{ username }}</span>
          </div>

          <div class="mt-6 flex gap-3">
            <button
              type="button"
              class="confirm-dialog-secondary flex-1 rounded-2xl px-4 py-3 text-sm font-semibold cursor-pointer"
              @click="closeDeleteConfirm"
            >
              取消
            </button>
            <button
              type="button"
              class="confirm-dialog-danger flex-1 rounded-2xl px-4 py-3 text-sm font-semibold cursor-pointer"
              :disabled="deleteSubmitting"
              @click="submitDeleteAccount"
            >
              {{ deleteSubmitting ? "注销中..." : "确认注销" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import MuiAccountSettingsAdapter from "./mui/MuiAccountSettingsAdapter.vue";
import { useAuthStore } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const props = defineProps<{
  open: boolean;
  username: string;
}>();

const emit = defineEmits<{
  close: [];
  sessionEnded: [reason: "password-changed" | "account-deleted"];
}>();

const authStore = useAuthStore();
const themeStore = useThemeStore();

const oldPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const deletePassword = ref("");
const showOldPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);
const showDeletePassword = ref(false);

const passwordError = ref("");
const deleteError = ref("");
const passwordSubmitting = ref(false);
const deleteSubmitting = ref(false);
const confirmingDeletion = ref(false);
const legacyAccountSettingsVisible = false;

const setOldPassword = (value: string) => {
  oldPassword.value = value;
};

const setNewPassword = (value: string) => {
  newPassword.value = value;
};

const setConfirmPassword = (value: string) => {
  confirmPassword.value = value;
};

const setDeletePassword = (value: string) => {
  deletePassword.value = value;
};

const toggleOldPassword = () => {
  showOldPassword.value = !showOldPassword.value;
};

const toggleNewPassword = () => {
  showNewPassword.value = !showNewPassword.value;
};

const toggleConfirmPassword = () => {
  showConfirmPassword.value = !showConfirmPassword.value;
};

const toggleDeletePassword = () => {
  showDeletePassword.value = !showDeletePassword.value;
};

const resetPasswordForm = () => {
  oldPassword.value = "";
  newPassword.value = "";
  confirmPassword.value = "";
  showOldPassword.value = false;
  showNewPassword.value = false;
  showConfirmPassword.value = false;
  passwordError.value = "";
};

const resetDeleteForm = () => {
  deletePassword.value = "";
  showDeletePassword.value = false;
  deleteError.value = "";
  confirmingDeletion.value = false;
};

const closeDeleteConfirm = () => {
  confirmingDeletion.value = false;
};

const closeModal = () => {
  resetPasswordForm();
  resetDeleteForm();
  emit("close");
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    if (confirmingDeletion.value) {
      closeDeleteConfirm();
      return;
    }
    closeModal();
  }
};

const submitPasswordChange = async () => {
  passwordError.value = "";
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    passwordError.value = "请完整填写旧密码和两次新密码";
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = "两次输入的新密码不一致";
    return;
  }
  passwordSubmitting.value = true;
  try {
    await authStore.changePassword(oldPassword.value, newPassword.value, confirmPassword.value);
    resetPasswordForm();
    closeModal();
    emit("sessionEnded", "password-changed");
  } catch (err) {
    passwordError.value = err instanceof Error ? err.message.replace(/^http \d+:\s*/, "") : "修改密码失败";
  } finally {
    passwordSubmitting.value = false;
  }
};

const openDeleteConfirm = () => {
  deleteError.value = "";
  if (!deletePassword.value) {
    deleteError.value = "请输入当前账户密码后再继续";
    return;
  }
  confirmingDeletion.value = true;
};

const submitDeleteAccount = async () => {
  deleteError.value = "";
  deleteSubmitting.value = true;
  try {
    await authStore.deleteAccount(deletePassword.value);
    resetDeleteForm();
    closeModal();
    emit("sessionEnded", "account-deleted");
  } catch (err) {
    confirmingDeletion.value = false;
    deleteError.value = err instanceof Error ? err.message.replace(/^http \d+:\s*/, "") : "注销账户失败";
  } finally {
    deleteSubmitting.value = false;
  }
};

watch(
  () => props.open,
  (next) => {
    if (!next) {
      resetPasswordForm();
      resetDeleteForm();
    }
  }
);

onMounted(() => {
  window.addEventListener("keydown", handleEscape);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleEscape);
});

defineExpose({
  resetPasswordForm,
  resetDeleteForm,
});
</script>

<style scoped>
.settings-input-wrap {
  position: relative;
}

.settings-input {
  width: 100%;
  min-height: 50px;
  border-radius: 18px;
  border: 1px solid color-mix(in srgb, var(--nav-border) 92%, white);
  background: rgba(255, 255, 255, 0.18);
  padding: 0.85rem 1rem;
  color: var(--app-text);
  outline: none;
  transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.settings-input-with-toggle {
  padding-right: 3.5rem;
}

.settings-input:focus {
  border-color: color-mix(in srgb, var(--nav-active-border) 82%, white);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--nav-active-border) 20%, transparent);
  background: rgba(255, 255, 255, 0.24);
}

.settings-visibility-btn {
  position: absolute;
  top: 50%;
  right: 0.9rem;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--nav-text-muted);
  transition: color 180ms ease, transform 180ms ease;
  cursor: pointer;
}

.settings-visibility-btn:hover {
  color: var(--app-text);
}

.settings-visibility-btn:focus-visible {
  outline: none;
  border-radius: 999px;
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--focus-ring-color) 28%, transparent);
}

.settings-visibility-btn-danger:hover {
  color: color-mix(in srgb, var(--tone-rose-text) 88%, var(--app-text));
}

.settings-input-danger:focus {
  border-color: rgba(251, 113, 133, 0.65);
  box-shadow: 0 0 0 4px rgba(251, 113, 133, 0.15);
}

.settings-primary-btn {
  min-height: 50px;
  width: 100%;
  border-radius: 18px;
  background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%);
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  box-shadow: 0 18px 34px rgba(56, 189, 248, 0.22);
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
  cursor: pointer;
}

.settings-primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 22px 38px rgba(56, 189, 248, 0.28);
}

.settings-primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.confirm-dialog {
  border: 1px solid color-mix(in srgb, var(--tone-rose-border) 68%, var(--nav-border));
  background: color-mix(in srgb, var(--glass-bg) 94%, var(--app-bg-1));
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.28);
}

.confirm-dialog-icon {
  background: color-mix(in srgb, var(--tone-rose-bg) 82%, transparent);
  color: var(--tone-rose-text);
}

.confirm-dialog-account {
  border: 1px solid color-mix(in srgb, var(--nav-border) 86%, transparent);
  background: color-mix(in srgb, var(--nav-bg) 58%, transparent);
}

.confirm-dialog-secondary {
  border: 1px solid color-mix(in srgb, var(--nav-border) 88%, transparent);
  background: color-mix(in srgb, var(--nav-bg) 52%, transparent);
  color: var(--app-text);
  transition: background 180ms ease, transform 180ms ease;
}

.confirm-dialog-secondary:hover {
  background: color-mix(in srgb, var(--nav-hover-bg-strong) 72%, var(--nav-bg));
}

.confirm-dialog-danger {
  border: 1px solid color-mix(in srgb, var(--tone-rose-border) 82%, transparent);
  background: color-mix(in srgb, var(--tone-rose-bg) 82%, transparent);
  color: color-mix(in srgb, var(--tone-rose-text) 82%, var(--app-text));
  transition: background 180ms ease, transform 180ms ease;
}

.confirm-dialog-danger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--tone-rose-bg) 96%, transparent);
}

.confirm-dialog-danger:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (prefers-reduced-motion: reduce) {
  .settings-input,
  .settings-primary-btn,
  .settings-visibility-btn,
  .confirm-dialog-secondary,
  .confirm-dialog-danger {
    transition: none;
  }
}
</style>
