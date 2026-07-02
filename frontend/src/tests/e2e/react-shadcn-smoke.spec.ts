import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test, type Page, type Route } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const screenshotDir = resolve(here, "../../../../screenshots");

const mockFiles = [
  {
    id: "file-pdf-1",
    filename: "chapter-1.pdf",
    originalName: "第1章.pdf",
    mimeType: "application/pdf",
    size: 1_280_000,
    uploadedAt: 1_735_000_000_000,
    url: "/storage/chapter-1.pdf",
    ragStatus: "ready",
    ragChunkCount: 18,
  },
  {
    id: "file-doc-2",
    filename: "experiment-notes.docx",
    originalName: "实验记录.docx",
    mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    size: 820_000,
    uploadedAt: 1_735_003_600_000,
    url: "/storage/experiment-notes.docx",
    ragStatus: "ready",
    ragChunkCount: 12,
  },
  {
    id: "file-md-3",
    filename: "summary.md",
    originalName: "复习提纲.md",
    mimeType: "text/markdown",
    size: 24_000,
    uploadedAt: 1_735_007_200_000,
    url: "/storage/summary.md",
    ragStatus: "pending",
    ragChunkCount: 0,
  },
];

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("edumind.react.auth.token", "mock-token");
    localStorage.setItem("edumind.react.theme", "dark");
    localStorage.setItem(
      "edumind.react.workspace",
      JSON.stringify({
        state: {
          role: "student",
          selectedMaterialIds: ["file-pdf-1", "file-doc-2"],
        },
        version: 0,
      }),
    );
  });

  await installApiMocks(page);
});

test("desktop shell, agent workflow, and file RAG stay usable", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Desktop-only smoke coverage.");
  const runtimeErrors = collectRuntimeErrors(page);

  await page.goto("/");
  await expect(page.getByText("React + shadcn/ui 新工作台")).toBeVisible();
  await expect(page.getByRole("link", { name: /项目首页/ })).toBeVisible();
  await expect(page.getByText("最近对话")).toBeVisible();
  await expect(page.getByText("学生功能")).toBeVisible();
  await takeScreenshot(page, "react-shadcn-dashboard-desktop.png");

  await page.goto("/workspace/chat");
  await expect(page.getByText("资料问答").first()).toBeVisible();
  await expect(page.getByText("学习交互文件夹")).toBeVisible();
  await expect(page.getByText("已选择 2 个文件进入 RAG")).toBeVisible();
  await page.getByPlaceholder(/根据这些 PDF|总结本章|所选资料/).fill("请综合两个文件说明共同重点");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("已检索 2 个文件、2 个片段")).toBeVisible();
  await expect(page.getByText(/Mock Agent 回答/)).toBeVisible();

  await page.goto("/files");
  await expect(page.getByText("上传文件").first()).toBeVisible();
  await expect(page.getByText("RAG 检索助手")).toBeVisible();
  await page.getByPlaceholder(/向所选资料提问/).fill("这些资料共同讨论了什么？");
  await page.getByRole("button", { name: /检索 2 个文件/ }).click();
  await expect(page.getByText(/跨文件上下文/)).toBeVisible();

  expect(runtimeErrors()).toEqual([]);
});

test("mobile file library has no horizontal overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "Mobile-only smoke coverage.");
  const runtimeErrors = collectRuntimeErrors(page);

  await page.goto("/files");
  await expect(page.getByText("文件库").first()).toBeVisible();
  await expect(page.getByText("RAG 检索助手")).toBeVisible();
  await takeScreenshot(page, "react-shadcn-files-mobile.png");

  const hasNoHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
  expect(hasNoHorizontalOverflow).toBe(true);
  expect(runtimeErrors()).toEqual([]);
});

async function installApiMocks(page: Page) {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const acceptsHtml = request.headers().accept?.includes("text/html") ?? false;

    if (!["127.0.0.1", "localhost"].includes(url.hostname)) {
      await route.continue();
      return;
    }

    if (path === "/auth/me") {
      await json(route, { ok: true, user: { id: 1, username: "熊骞" } });
      return;
    }
    if (path === "/auth/logout") {
      await json(route, { ok: true });
      return;
    }
    if (path === "/chats") {
      await json(route, {
        ok: true,
        chats: [
          { id: "chat-1", title: "函数复习", createdAt: 1_735_000_000_000 },
          { id: "chat-2", title: "实验设计讨论", createdAt: 1_735_001_000_000 },
        ],
      });
      return;
    }
    if (path === "/chats/chat-1") {
      await json(route, {
        ok: true,
        chat: { id: "chat-1", title: "函数复习" },
        messages: [
          { role: "user", content: "请解释函数极限", at: 1_735_000_000_000 },
          { role: "assistant", content: "可以从邻域和趋势两层理解。", at: 1_735_000_010_000 },
        ],
      });
      return;
    }
    if (path === "/files" && method === "GET" && !acceptsHtml) {
      await json(route, { ok: true, files: mockFiles });
      return;
    }
    if (path === "/files/rag/search") {
      await json(route, {
        ok: true,
        context: "跨文件上下文：第1章.pdf 和 实验记录.docx 都讨论了变量、证据和结论之间的关系。",
        files: mockFiles.slice(0, 2),
        chunks: [{ fileId: "file-pdf-1" }, { fileId: "file-doc-2" }],
        failedFiles: [],
      });
      return;
    }
    if (["/chat", "/quiz", "/paper", "/lesson-plan", "/smartnotes", "/podcast", "/slides/generate"].includes(path)) {
      await json(route, { ok: true, answer: "Mock Agent 回答：已经整合多份资料，并生成可继续追问的结论。" });
      return;
    }
    if (["/quizzes", "/papers", "/lesson-plans", "/slides", "/flashcards", "/teaching-videos", "/exams"].includes(path)) {
      await json(route, { ok: true, items: [], quizzes: [], papers: [], lessonPlans: [], slides: [] });
      return;
    }
    if (path === "/wrongbook/summary") {
      await json(route, { ok: true, stats: {}, masteryTrend: [], weakTopics: [] });
      return;
    }
    if (path === "/speaking/history") {
      await json(route, { ok: true, history: [] });
      return;
    }
    if (path === "/api/bilibili/search") {
      await json(route, { ok: true, items: [{ title: "函数学习视频", author: "EduMind" }] });
      return;
    }

    await route.continue();
  });
}

async function json(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

function collectRuntimeErrors(page: Page) {
  const messages: string[] = [];
  page.on("pageerror", (error) => messages.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") messages.push(message.text());
  });
  return () => messages;
}

async function takeScreenshot(page: Page, filename: string) {
  mkdirSync(screenshotDir, { recursive: true });
  await page.screenshot({ path: resolve(screenshotDir, filename), fullPage: true });
}
