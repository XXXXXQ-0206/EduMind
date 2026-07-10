import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Clock3, FileDown, History, ListChecks, SlidersHorizontal } from "lucide-react";
import { AgentConversationPanel, type AgentMessage, type QuickPrompt } from "@/components/patterns/agent-conversation";
import { MaterialPicker } from "@/components/patterns/material-picker";
import { Alert } from "@/components/ui/alert";
import { AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, subscribeTaskEvents, type ChatInfo, type ChatMessage, type SlideRecord, type SlideWorkflowResult, type TaskEvent } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";
import { workflowByKind, type FeatureKind } from "@/config/navigation";
import { useTaskStore } from "@/stores/task-store";
import { useWorkspaceStore } from "@/stores/workspace-store";

const quickPromptsByKind: Partial<Record<FeatureKind, QuickPrompt[]>> = {
  chat: [
    { label: "总结资料重点", value: "请根据所选资料总结三条核心观点，并列出需要复习的概念。" },
    { label: "解释难点", value: "请用通俗语言解释资料里最容易混淆的知识点，并给一个例子。" },
    { label: "生成追问题", value: "请基于资料提出5个适合继续追问的问题。" },
  ],
  quiz: [
    { label: "生成5题", value: "围绕所选资料生成5道中等难度测验题，并给出答案解析。" },
    { label: "薄弱点自测", value: "根据资料设计一组能暴露薄弱点的自测题。" },
  ],
  paper: [
    { label: "单元试卷", value: "生成一份覆盖基础题、综合题和应用题的单元试卷。" },
    { label: "课堂小测", value: "生成一份15分钟课堂小测，题目要便于投屏讲解。" },
  ],
  "lesson-plan": [
    { label: "完整教案", value: "请生成一份包含教学目标、重难点、课堂流程和板书设计的教案。" },
    { label: "互动课堂", value: "请围绕所选资料设计课堂互动问题和分层任务。" },
  ],
  slides: [
    { label: "课件大纲", value: "请生成一套教学幻灯片大纲，每页包含标题、要点和讲解提示。" },
    { label: "图文课件", value: "请生成适合课堂展示的图文课件结构，并标注需要配图的位置。" },
  ],
  smartnotes: [
    { label: "整理笔记", value: "请把所选资料整理为结构化笔记，包含概念、公式、例题和易错点。" },
    { label: "考前复习", value: "请生成一份考前复习提纲，并标出优先复习顺序。" },
  ],
  podcast: [
    { label: "播客脚本", value: "请把所选资料改写成双人播客脚本，语气自然，适合复习收听。" },
    { label: "知识串讲", value: "请生成一个5分钟知识串讲脚本，先讲概念再讲例子。" },
  ],
};

type SlideExportInfo = Pick<SlideWorkflowResult, "slideId" | "title" | "pageCount" | "pptxReady" | "downloadUrl">;

export function WorkspacePage() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const kind = (params.kind || "chat") as FeatureKind;
  const workflow = workflowByKind(kind);
  const { role, setRole, files, setFiles, selectedMaterialIds, toggleMaterial, clearMaterials } = useWorkspaceStore();
  const { current, start, push, reset } = useTaskStore();
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [recentChats, setRecentChats] = useState<ChatInfo[]>([]);
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState("5");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [slideExport, setSlideExport] = useState<SlideExportInfo | null>(null);
  const [slideHistory, setSlideHistory] = useState<SlideRecord[]>([]);
  const [slideHistoryError, setSlideHistoryError] = useState("");

  useEffect(() => {
    const nextRole = searchParams.get("role");
    if (nextRole === "teacher" || workflow.role === "teacher") setRole("teacher");
    else if (nextRole === "student" || workflow.role === "student") setRole("student");
  }, [searchParams, workflow.role, setRole]);

  useEffect(() => {
    void api.listFiles(role).then((result) => setFiles(result.files)).catch(() => setFiles([]));
    void api.listChats(role).then((result) => setRecentChats(result.chats || [])).catch(() => setRecentChats([]));
  }, [role, setFiles]);

  useEffect(() => {
    if (workflow.kind !== "slides") {
      setSlideHistory([]);
      setSlideHistoryError("");
      return;
    }
    void api
      .listSlides()
      .then((result) => {
        setSlideHistory(result.slides || []);
        setSlideHistoryError("");
      })
      .catch((err) => {
        setSlideHistory([]);
        setSlideHistoryError(err instanceof Error ? err.message : "历史幻灯片加载失败");
      });
  }, [workflow.kind]);

  useEffect(() => {
    const chatId = searchParams.get("chatId");
    if (!chatId) return;
    void api
      .getChat(chatId)
      .then((result) => {
        const nextMessages = normalizeChatMessages(result.messages);
        setMessages(nextMessages);
      })
      .catch(() => undefined);
  }, [searchParams]);

  const selectedFiles = useMemo(() => files.filter((file) => selectedMaterialIds.includes(file.id)), [files, selectedMaterialIds]);
  const progress = useMemo(() => progressFor(current?.phase, current?.status), [current]);
  const progressLabel = current ? `${current.kind} / ${current.phase}` : "等待任务";
  const quickPrompts = quickPromptsByKind[workflow.kind] || quickPromptsByKind.chat || [];

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setError("");
    setBusy(true);
    setSlideExport(null);
    reset();
    setMessages((items) => [
      ...items,
      { id: `u-${Date.now()}`, role: "user", content: trimmed, meta: role === "teacher" ? "教师输入" : "学生输入" },
    ]);

    try {
      const ragMessage = await prepareRagContext(trimmed);
      if (ragMessage) setMessages((items) => [...items, ragMessage]);

      const payload = buildPayload(trimmed);
      const result = await api.startWorkflow(workflow.kind, payload);
      const taskId = String(
        result.chatId || result.quizId || result.paperId || result.noteId || result.pid || result.slideId || result.lessonPlanId || Date.now(),
      );
      start(workflow.kind, taskId);

      if (result.events) {
        const close = subscribeTaskEvents(
          String(result.events),
          (event) => handleTaskEvent(event, close),
          (err) => {
            setError(err.message);
            setBusy(false);
          },
        );
      } else {
        push({ type: "done", result });
        const nextSlideExport = extractSlideExport(result);
        if (nextSlideExport) setSlideExport(nextSlideExport);
        if (workflow.kind === "slides") {
          void api.listSlides().then((history) => setSlideHistory(history.slides || [])).catch(() => undefined);
        }
        setMessages((items) => [
          ...items,
          {
            id: `a-${Date.now()}`,
            role: "assistant",
            content: workflow.kind === "slides" && nextSlideExport ? "课件已生成，可在上方或历史幻灯片中下载 PPT 文件。" : stringifyOutput(result),
            meta: "任务已完成",
          },
        ]);
        setBusy(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "任务启动失败";
      setError(message);
      setMessages((items) => [...items, { id: `e-${Date.now()}`, role: "assistant", content: `抱歉，任务失败：${message}` }]);
      setBusy(false);
    }
  }

  async function prepareRagContext(query: string): Promise<AgentMessage | null> {
    if (!selectedMaterialIds.length) {
      return {
        id: `r-${Date.now()}`,
        role: "system",
        meta: "RAG",
        content: "当前未选择资料，Agent 将直接基于输入内容执行。",
      };
    }
    const result = await api.ragSearch(query, role, selectedMaterialIds);
    const fileCount = result.files.length;
    const chunkCount = result.chunks.length;
    return {
      id: `r-${Date.now()}`,
      role: "system",
      meta: "RAG 检索完成",
      content: `已检索 ${fileCount} 个文件、${chunkCount} 个片段。\n${result.context ? result.context.slice(0, 900) : "没有检索到直接上下文。"}`,
    };
  }

  function buildPayload(prompt: string) {
    const includeMaterials = selectedMaterialIds.length > 0;
    const base = { includeMaterials, materialIds: selectedMaterialIds, role, topic: prompt, q: prompt };
    if (workflow.kind === "quiz") return { ...base, count: Number(count), difficulty };
    if (workflow.kind === "paper") return { ...base, difficulty, count_choice: 10, count_fill: 5, count_application: 2 };
    if (workflow.kind === "slides") return { ...base, pageCount: Math.max(5, Number(count)) };
    return base;
  }

  function handleTaskEvent(event: TaskEvent, close: () => void) {
    push(event);
    if (event.type === "error") {
      const message = String(event.error || "生成失败");
      setError(message);
      setMessages((items) => [...items, { id: `err-${Date.now()}`, role: "assistant", content: `生成失败：${message}` }]);
      setBusy(false);
      close();
      return;
    }
    const answer = extractAnswer(event);
    const nextSlideExport = extractSlideExport(event.result ?? event);
    if (nextSlideExport) setSlideExport(nextSlideExport);
    if (answer) {
      setMessages((items) => [...items, { id: `a-${Date.now()}`, role: "assistant", content: answer, meta: "Agent 输出" }]);
    }
    if (event.type === "done") {
      setBusy(false);
      close();
    }
  }

  return (
    <AgentConversationPanel
      eyebrow={workflow.role === "teacher" ? "教师生成" : "学生学习"}
      title={workflow.title}
      description={workflow.description}
      placeholder={workflow.promptPlaceholder}
      messages={messages}
      quickPrompts={quickPrompts}
      busy={busy}
      progress={progress}
      progressLabel={progressLabel}
      contextFiles={selectedFiles}
      selectedCount={selectedMaterialIds.length}
      onSubmit={submit}
      side={
        <WorkspaceSide
          role={role}
          workflowKind={workflow.kind}
          files={files}
          selectedIds={selectedMaterialIds}
          recentChats={recentChats}
          slideHistory={slideHistory}
          slideHistoryError={slideHistoryError}
          difficulty={difficulty}
          count={count}
          onDifficultyChange={setDifficulty}
          onCountChange={setCount}
          onToggle={toggleMaterial}
          onClear={clearMaterials}
        />
      }
      result={
        <>
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>任务异常</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {workflow.kind === "slides" && slideExport ? <SlidePptxExportPanel info={slideExport} /> : null}
        </>
      }
    />
  );
}

function SlidePptxExportPanel({ info }: { info: SlideExportInfo }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  async function downloadPptx() {
    setDownloadError("");
    setDownloading(true);
    try {
      await saveSlidePptx(info.slideId);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "PPT 下载失败");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Card className="border-primary/20 bg-primary/5 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <FileDown className="size-4 text-primary" />
          PPT 下载
        </CardTitle>
        <CardDescription>
          {info.pptxReady ? "已按固定模板生成 PPT 文件。" : "可将当前图文课件移植为 PPT 文件。"}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 text-sm">
          <p className="truncate font-medium">{info.title || "教学幻灯片"}</p>
          <p className="text-xs text-muted-foreground">{info.pageCount ? `${info.pageCount} 页` : "课件文件"} · {info.slideId}</p>
        </div>
        <Button type="button" onClick={() => void downloadPptx()} loading={downloading}>
          <FileDown className="size-4" />
          移植到ppt文件
        </Button>
        {downloadError ? <p className="text-sm text-destructive sm:basis-full">{downloadError}</p> : null}
      </CardContent>
    </Card>
  );
}

function WorkspaceSide({
  role,
  workflowKind,
  files,
  selectedIds,
  recentChats,
  slideHistory,
  slideHistoryError,
  difficulty,
  count,
  onDifficultyChange,
  onCountChange,
  onToggle,
  onClear,
}: {
  role: "student" | "teacher";
  workflowKind: FeatureKind;
  files: ReturnType<typeof useWorkspaceStore.getState>["files"];
  selectedIds: string[];
  recentChats: ChatInfo[];
  slideHistory: SlideRecord[];
  slideHistoryError: string;
  difficulty: string;
  count: string;
  onDifficultyChange: (value: string) => void;
  onCountChange: (value: string) => void;
  onToggle: (id: string) => void;
  onClear: () => void;
}) {
  return (
    <>
      <MaterialPicker
        files={files}
        selectedIds={selectedIds}
        onToggle={onToggle}
        onClear={onClear}
        label={role === "teacher" ? "教学交互文件夹" : "学习交互文件夹"}
        compact
      />
      <Card className="gap-4">
        <CardHeader className="pb-0">
          <CardTitle className="flex items-center gap-2 text-sm">
            <SlidersHorizontal className="size-4 text-primary" />
            任务参数
          </CardTitle>
          <CardDescription>不同工作流会读取适用参数。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="grid gap-2">
            <Label>难度</Label>
            <Select value={difficulty} onValueChange={onDifficultyChange}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="easy">简单</SelectItem>
                <SelectItem value="medium">中等</SelectItem>
                <SelectItem value="hard">困难</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>{workflowKind === "slides" ? "页数" : "数量"}</Label>
            <Select value={count} onValueChange={onCountChange}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5</SelectItem>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="15">15</SelectItem>
                <SelectItem value="20">20</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {workflowKind === "slides" ? (
        <SlideHistoryCard slides={slideHistory} error={slideHistoryError} />
      ) : (
        <RecentChatsCard role={role} workflowKind={workflowKind} recentChats={recentChats} />
      )}
    </>
  );
}

function SlideHistoryCard({ slides, error }: { slides: SlideRecord[]; error: string }) {
  const [downloadingId, setDownloadingId] = useState("");
  const [downloadError, setDownloadError] = useState("");

  async function download(slideId: string) {
    setDownloadError("");
    setDownloadingId(slideId);
    try {
      await saveSlidePptx(slideId);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "PPT 下载失败");
    } finally {
      setDownloadingId("");
    }
  }

  return (
    <Card className="gap-4">
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-sm">
          <History className="size-4 text-primary" />
          历史幻灯片
        </CardTitle>
        <CardDescription>历史课件也可以直接移植为 PPT 文件。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {error ? <p className="rounded-md border border-destructive/30 p-3 text-xs leading-5 text-destructive">{error}</p> : null}
        {downloadError ? <p className="rounded-md border border-destructive/30 p-3 text-xs leading-5 text-destructive">{downloadError}</p> : null}
        {slides.length ? (
          slides.slice(0, 6).map((slide) => (
            <div key={slide.id} className="rounded-md border bg-muted/20 p-2 text-sm">
              <div className="flex min-w-0 items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <ListChecks className="size-4 shrink-0 text-muted-foreground" />
                    <span className="truncate font-medium">{slide.title || "未命名课件"}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock3 className="size-3" />
                    {formatDate(slide.updated_at || slide.created_at || slide.at)}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => void download(slide.id)}
                  loading={downloadingId === slide.id}
                  aria-label={`下载 ${slide.title || "课件"} 的 PPT`}
                >
                  <FileDown className="size-3" />
                  PPT
                </Button>
              </div>
            </div>
          ))
        ) : (
          <p className="rounded-md border border-dashed p-3 text-xs leading-5 text-muted-foreground">暂无历史幻灯片。</p>
        )}
      </CardContent>
    </Card>
  );
}

function RecentChatsCard({
  role,
  workflowKind,
  recentChats,
}: {
  role: "student" | "teacher";
  workflowKind: FeatureKind;
  recentChats: ChatInfo[];
}) {
  return (
    <Card className="gap-4">
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-sm">
          <History className="size-4 text-primary" />
          最近对话
        </CardTitle>
        <CardDescription>与旧前端相同的历史入口位置。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {recentChats.length ? (
          recentChats.slice(0, 6).map((chat) => (
            <Link
              key={chat.id}
              to={`/workspace/chat?chatId=${encodeURIComponent(chat.id)}&role=${role}`}
              className={cn(
                "block rounded-md border bg-muted/20 p-2 text-sm transition-colors hover:bg-muted",
                workflowKind === "chat" && "hover:border-primary/30",
              )}
            >
              <div className="flex items-center gap-2">
                <ListChecks className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate font-medium">{chat.title || "未命名对话"}</span>
              </div>
              <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <Clock3 className="size-3" />
                {formatDate(chat.updated_at || chat.createdAt)}
              </div>
            </Link>
          ))
        ) : (
          <p className="rounded-md border border-dashed p-3 text-xs leading-5 text-muted-foreground">暂无历史对话。</p>
        )}
      </CardContent>
    </Card>
  );
}

async function saveSlidePptx(slideId: string) {
  const { blob, filename } = await api.downloadSlidePptx(slideId);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1200);
}

function normalizeChatMessages(items: ChatMessage[]): AgentMessage[] {
  return items.map((message, index) => ({
    id: `${message.role}-${message.at || index}`,
    role: message.role,
    content: message.content,
    meta: message.role === "assistant" ? "历史回答" : "历史提问",
  }));
}

function progressFor(phase?: string, status?: string) {
  if (status === "done" || phase === "done") return 100;
  if (status === "error") return 100;
  if (phase === "packaging") return 82;
  if (phase === "generating") return 56;
  if (phase === "ready") return 24;
  return status === "running" ? 35 : 0;
}

function extractSlideExport(value: unknown): SlideExportInfo | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  if (typeof record.slideId === "string") {
    return {
      slideId: record.slideId,
      title: typeof record.title === "string" ? record.title : undefined,
      pageCount: typeof record.pageCount === "number" ? record.pageCount : undefined,
      pptxReady: typeof record.pptxReady === "boolean" ? record.pptxReady : undefined,
      downloadUrl: typeof record.downloadUrl === "string" ? record.downloadUrl : undefined,
    };
  }
  return extractSlideExport(record.result);
}

function extractAnswer(event: TaskEvent) {
  const output = event.answer ?? event.quiz ?? event.paper ?? event.notes ?? event.script ?? event.slides ?? event.result;
  if (!output) return "";
  return stringifyOutput(output);
}

function stringifyOutput(output: unknown) {
  if (typeof output === "string") return output;
  return JSON.stringify(output, null, 2);
}
