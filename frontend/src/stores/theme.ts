import { defineStore } from "pinia";
import { ref } from "vue";
import { migrateStorageKey } from "../lib/userStorage";

type ThemeMode = "dark" | "light";

const STORAGE_KEY = "edumind-theme";
const LEGACY_STORAGE_KEY = ["page", "lm-theme"].join("");

function applyTheme(mode: ThemeMode) {
  const root = document.documentElement;
  root.classList.remove("theme-dark", "theme-light");
  root.classList.add(mode === "dark" ? "theme-dark" : "theme-light");
  root.classList.toggle("dark", mode === "dark");
  root.style.colorScheme = mode;
}

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<ThemeMode>((migrateStorageKey(STORAGE_KEY, LEGACY_STORAGE_KEY) as ThemeMode) || "dark");

  const setMode = (next: ThemeMode) => {
    mode.value = next;
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  };

  const toggle = () => setMode(mode.value === "dark" ? "light" : "dark");

  const init = () => {
    applyTheme(mode.value);
  };

  return { mode, setMode, toggle, init };
});
