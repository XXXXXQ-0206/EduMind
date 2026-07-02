import { describe, expect, it } from "vitest";
import { apiUrl } from "@/config/env";

describe("apiUrl", () => {
  it("keeps absolute urls unchanged", () => {
    expect(apiUrl("https://example.com/auth/me")).toBe("https://example.com/auth/me");
  });

  it("normalizes relative paths", () => {
    expect(apiUrl("auth/me")).toMatch(/\/auth\/me$/);
    expect(apiUrl("/files")).toMatch(/\/files$/);
  });
});
