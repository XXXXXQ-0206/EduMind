import { create } from "zustand";
import type { FeatureKind } from "@/config/navigation";
import type { TaskEvent } from "@/lib/api";

export type TaskProgress = {
  id: string;
  kind: FeatureKind;
  phase: string;
  status: "idle" | "running" | "done" | "error";
  events: TaskEvent[];
  output?: unknown;
  error?: string;
};

type TaskState = {
  current: TaskProgress | null;
  start: (kind: FeatureKind, id: string) => void;
  push: (event: TaskEvent) => void;
  reset: () => void;
};

export const useTaskStore = create<TaskState>((set) => ({
  current: null,
  start: (kind, id) => set({ current: { kind, id, phase: "queued", status: "running", events: [] } }),
  push: (event) =>
    set((state) => {
      if (!state.current) return state;
      const status = event.type === "done" ? "done" : event.type === "error" ? "error" : "running";
      const output = event.answer ?? event.quiz ?? event.paper ?? event.notes ?? event.script ?? event.slides ?? state.current.output;
      return {
        current: {
          ...state.current,
          status,
          phase: String(event.value || event.type),
          events: [...state.current.events, event].slice(-60),
          output,
          error: typeof event.error === "string" ? event.error : state.current.error,
        },
      };
    }),
  reset: () => set({ current: null }),
}));
