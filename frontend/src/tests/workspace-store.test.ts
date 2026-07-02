import { beforeEach, describe, expect, it } from "vitest";
import { useWorkspaceStore } from "@/stores/workspace-store";

describe("workspace store", () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ role: "student", selectedMaterialIds: [], files: [] });
  });

  it("toggles selected materials", () => {
    useWorkspaceStore.getState().toggleMaterial("file-1");
    expect(useWorkspaceStore.getState().selectedMaterialIds).toEqual(["file-1"]);
    useWorkspaceStore.getState().toggleMaterial("file-1");
    expect(useWorkspaceStore.getState().selectedMaterialIds).toEqual([]);
  });

  it("clears materials when role changes", () => {
    useWorkspaceStore.getState().toggleMaterial("file-1");
    useWorkspaceStore.getState().setRole("teacher");
    expect(useWorkspaceStore.getState().role).toBe("teacher");
    expect(useWorkspaceStore.getState().selectedMaterialIds).toEqual([]);
  });
});
