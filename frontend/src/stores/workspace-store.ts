import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Role } from "@/config/navigation";
import type { LibraryFile } from "@/lib/api";

type WorkspaceState = {
  role: Role;
  selectedMaterialIds: string[];
  files: LibraryFile[];
  setRole: (role: Role) => void;
  setFiles: (files: LibraryFile[]) => void;
  toggleMaterial: (id: string) => void;
  clearMaterials: () => void;
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      role: "student",
      selectedMaterialIds: [],
      files: [],
      setRole: (role) => set((state) => (state.role === role ? {} : { role, selectedMaterialIds: [] })),
      setFiles: (files) => set({ files }),
      toggleMaterial: (id) =>
        set((state) => ({
          selectedMaterialIds: state.selectedMaterialIds.includes(id)
            ? state.selectedMaterialIds.filter((item) => item !== id)
            : [...state.selectedMaterialIds, id],
        })),
      clearMaterials: () => set({ selectedMaterialIds: [] }),
    }),
    {
      name: "edumind.react.workspace",
      partialize: (state) => ({ role: state.role, selectedMaterialIds: state.selectedMaterialIds }),
    },
  ),
);
