import { defineStore } from "pinia";
import { computed, ref } from "vue";
import {
  changePassword as changePasswordAPI,
  deleteAccount as deleteAccountAPI,
  getCurrentSession,
  login as loginAPI,
  logout as logoutAPI,
  register as registerAPI,
} from "../lib/api";
import { readAuthSession, type AuthSession, writeAuthSession } from "../lib/auth";

export const useAuthStore = defineStore("auth", () => {
  const session = ref<AuthSession | null>(readAuthSession());
  const hydrated = ref(false);

  const isAuthenticated = computed(() => Boolean(session.value?.token));
  const username = computed(() => session.value?.user?.username || "");
  const token = computed(() => session.value?.token || "");
  const user = computed(() => session.value?.user || null);

  const setSession = (next: AuthSession | null) => {
    session.value = next;
    writeAuthSession(next);
  };

  const hydrate = async () => {
    if (hydrated.value) return;
    hydrated.value = true;
    if (!session.value?.token) return;
    try {
      const res = await getCurrentSession();
      setSession({ token: session.value.token, user: res.user });
    } catch {
      setSession(null);
    }
  };

  const login = async (username: string, password: string) => {
    const res = await loginAPI(username, password);
    setSession({ token: res.token, user: res.user });
    return res;
  };

  const register = async (username: string, password: string) => {
    const res = await registerAPI(username, password);
    setSession({ token: res.token, user: res.user });
    return res;
  };

  const logout = async () => {
    try {
      if (session.value?.token) {
        await logoutAPI();
      }
    } catch {
      // Keep logout resilient if the session has already expired.
    } finally {
      setSession(null);
    }
  };

  const clearSession = () => {
    setSession(null);
  };

  const changePassword = async (oldPassword: string, newPassword: string, confirmPassword: string) => {
    await changePasswordAPI(oldPassword, newPassword, confirmPassword);
    setSession(null);
  };

  const deleteAccount = async (password: string) => {
    await deleteAccountAPI(password);
    setSession(null);
  };

  return {
    session,
    user,
    username,
    token,
    isAuthenticated,
    hydrate,
    setSession,
    login,
    register,
    logout,
    clearSession,
    changePassword,
    deleteAccount,
  };
});
