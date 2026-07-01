import { defineStore } from "pinia";
import { ref } from "vue";
import { migrateStorageKey } from "../lib/userStorage";

type UserRole = "teacher" | "student";

const STORAGE_KEY = "edumind-role";
const LEGACY_STORAGE_KEY = ["page", "lm-role"].join("");

export const useRoleStore = defineStore("role", () => {
  const stored = migrateStorageKey(STORAGE_KEY, LEGACY_STORAGE_KEY);
  const initialRole = stored === "teacher" || stored === "student" ? stored : "student";
  const role = ref<UserRole>(initialRole);

  if (stored !== initialRole) {
    localStorage.setItem(STORAGE_KEY, initialRole);
  }

  const setRole = (next: UserRole) => {
    role.value = next;
    localStorage.setItem(STORAGE_KEY, next);
  };

  return { role, setRole };
});
