import { defineStore } from "pinia";
import { ref } from "vue";

type UserRole = "teacher" | "student";

const STORAGE_KEY = "pagelm-role";

export const useRoleStore = defineStore("role", () => {
  const stored = localStorage.getItem(STORAGE_KEY);
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
