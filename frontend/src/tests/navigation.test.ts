import { describe, expect, it } from "vitest";
import { navSections, workflowByKind, workflowDefinitions } from "@/config/navigation";
import { router } from "@/router";

describe("navigation configuration", () => {
  it("keeps workflow definitions data-driven and routeable", () => {
    expect(workflowDefinitions.length).toBeGreaterThanOrEqual(6);
    expect(workflowByKind("paper").role).toBe("teacher");
    expect(workflowByKind("chat").endpoint).toBe("chat");
  });

  it("contains stable top-level destinations", () => {
    const hrefs = navSections.flatMap((section) => section.items.map((item) => item.href));
    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/files");
    expect(hrefs).toContain("/workspace/chat");
    expect(hrefs).toContain("/workspace/chat?role=teacher");
    expect(hrefs).toContain("/teacher/bili-learning");
    expect(hrefs).toContain("/english-speaking");
  });

  it("keeps legacy feature paths in the router tree", () => {
    const paths = router.routes.flatMap((route) => route.children?.map((child) => child.path) ?? []);
    expect(paths).toContain("wrong-book");
    expect(paths).toContain("teaching-video");
    expect(paths).toContain("english-speaking");
    expect(paths).toContain("planner");
  });
});
