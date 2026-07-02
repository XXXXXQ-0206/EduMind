import { create } from "zustand";
import { clearAuthToken, getAuthToken } from "@/lib/auth";
import { api, type AuthUser } from "@/lib/api";

type AuthState = {
  token: string;
  user: AuthUser | null;
  status: "idle" | "loading" | "authenticated" | "anonymous";
  error: string;
  restore: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: getAuthToken(),
  user: null,
  status: getAuthToken() ? "loading" : "anonymous",
  error: "",
  async restore() {
    if (!getAuthToken()) {
      set({ status: "anonymous", user: null });
      return;
    }
    set({ status: "loading", error: "" });
    try {
      const session = await api.me();
      set({ user: session.user, status: "authenticated", token: getAuthToken() });
    } catch (error) {
      clearAuthToken();
      set({ user: null, token: "", status: "anonymous", error: error instanceof Error ? error.message : "登录已失效" });
    }
  },
  async login(username, password) {
    set({ status: "loading", error: "" });
    try {
      const session = await api.login(username, password);
      set({ token: session.token, user: session.user, status: "authenticated" });
    } catch (error) {
      set({ status: "anonymous", error: error instanceof Error ? error.message : "登录失败" });
      throw error;
    }
  },
  async register(username, password) {
    set({ status: "loading", error: "" });
    try {
      const session = await api.register(username, password);
      set({ token: session.token, user: session.user, status: "authenticated" });
    } catch (error) {
      set({ status: "anonymous", error: error instanceof Error ? error.message : "注册失败" });
      throw error;
    }
  },
  async logout() {
    try {
      await api.logout();
    } catch {
      // Local logout should continue even if the session endpoint is unavailable.
    }
    clearAuthToken();
    set({ token: "", user: null, status: "anonymous" });
  },
}));
