import { useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  Bot,
  CheckCircle2,
  CornerDownLeft,
  FileText,
  Loader2,
  Paperclip,
  Sparkles,
  UserRound,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { cn, formatBytes } from "@/lib/utils";
import type { LibraryFile } from "@/lib/api";

export type AgentMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: ReactNode;
  meta?: string;
};

export type QuickPrompt = {
  label: string;
  value: string;
};

export function AgentConversationPanel({
  title,
  description,
  eyebrow,
  placeholder,
  messages,
  quickPrompts = [],
  busy = false,
  progress = 0,
  progressLabel = "等待任务",
  contextFiles = [],
  selectedCount = 0,
  side,
  result,
  onSubmit,
  className,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  placeholder: string;
  messages: AgentMessage[];
  quickPrompts?: QuickPrompt[];
  busy?: boolean;
  progress?: number;
  progressLabel?: string;
  contextFiles?: LibraryFile[];
  selectedCount?: number;
  side?: ReactNode;
  result?: ReactNode;
  onSubmit: (text: string) => void | Promise<void>;
  className?: string;
}) {
  const [draft, setDraft] = useState("");
  const visibleMessages = useMemo(() => messages.filter(Boolean), [messages]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    await onSubmit(text);
  }

  async function submitQuick(value: string) {
    if (busy) return;
    setDraft("");
    await onSubmit(value);
  }

  return (
    <div className={cn("grid min-h-[calc(100dvh-6.5rem)] gap-4 xl:grid-cols-[18rem_minmax(0,1fr)]", className)}>
      <aside className="min-h-0 space-y-4 xl:sticky xl:top-20 xl:h-[calc(100dvh-6.75rem)]">
        {side}
        <Card className="gap-4">
          <CardHeader className="pb-0">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Paperclip className="size-4 text-primary" />
              上下文资料
            </CardTitle>
            <CardDescription>已选择 {selectedCount} 个文件进入 RAG。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {contextFiles.length ? (
              contextFiles.slice(0, 5).map((file) => (
                <div key={file.id} className="rounded-md border bg-muted/30 p-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <FileText className="size-4 shrink-0 text-muted-foreground" />
                    <p className="truncate text-xs font-medium">{file.originalName || file.filename}</p>
                  </div>
                  <div className="mt-1 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                    <span>{formatBytes(file.size)}</span>
                    <Badge variant={file.ragStatus === "ready" ? "success" : "outline"}>{file.ragStatus || "pending"}</Badge>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-dashed bg-muted/20 p-3 text-xs leading-5 text-muted-foreground">
                在文件库或左侧资料栏选择文件后，Agent 会在调用前自动检索相关片段。
              </div>
            )}
          </CardContent>
        </Card>
      </aside>

      <section className="min-w-0 rounded-[6px] border bg-card/82 shadow-none">
        <div className="flex min-h-[calc(100dvh-6.5rem)] flex-col">
          <div className="border-b px-4 py-4 sm:px-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                {eyebrow ? <p className="text-xs font-medium text-primary">{eyebrow}</p> : null}
                <h2 className="mt-1 text-xl font-semibold tracking-normal">{title}</h2>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
              </div>
              <div className="min-w-44 rounded-md border bg-muted/30 p-3">
                <div className="mb-2 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>{progressLabel}</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} />
              </div>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-5">
            {visibleMessages.length ? (
              <div className="mx-auto flex max-w-4xl flex-col gap-4">
                {result}
                {visibleMessages.map((message) => (
                  <AgentBubble key={message.id} message={message} />
                ))}
                {busy ? <AgentThinking /> : null}
              </div>
            ) : (
              <div className="mx-auto grid min-h-[46vh] max-w-4xl place-items-center">
                <div className="w-full text-center">
                  <div className="mx-auto grid size-14 place-items-center rounded-[6px] border bg-muted/40 text-primary shadow-none">
                    <Sparkles className="size-6" />
                  </div>
                  <h3 className="mt-4 text-2xl font-semibold tracking-normal">{title}</h3>
                  <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>
                  {quickPrompts.length ? (
                    <div className="mt-6 flex flex-wrap justify-center gap-2">
                      {quickPrompts.map((prompt) => (
                        <Button key={prompt.value} type="button" variant="outline" size="sm" onClick={() => void submitQuick(prompt.value)}>
                          {prompt.label}
                        </Button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            )}
          </div>

          <div className="border-t bg-card/95 px-3 py-3">
            <form onSubmit={(event) => void submit(event)} className="mx-auto max-w-4xl">
              <div className="rounded-[6px] border bg-background/45 p-2 shadow-none focus-within:ring-[3px] focus-within:ring-ring/30">
                <Textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder={placeholder}
                  className="max-h-40 min-h-20 resize-none border-0 bg-transparent p-2 shadow-none focus-visible:ring-0"
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                      void submit();
                    }
                  }}
                />
                <div className="flex items-center justify-between gap-2 px-2 pb-1">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className="rounded-md">
                      Ctrl Enter 发送
                    </Badge>
                    <span className="hidden sm:inline">Agent 会先检索资料，再启动任务。</span>
                  </div>
                  <Button type="submit" disabled={!draft.trim() || busy} loading={busy} aria-label="发送">
                    <CornerDownLeft className="size-4" />
                    发送
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}

function AgentBubble({ message }: { message: AgentMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const Icon = isUser ? UserRound : isSystem ? CheckCircle2 : Bot;

  return (
    <div className={cn("flex gap-3", isUser && "justify-end")}>
      {!isUser ? (
        <div className="grid size-8 shrink-0 place-items-center rounded-md border bg-muted text-muted-foreground">
          <Icon className="size-4" />
        </div>
      ) : null}
      <div
        className={cn(
          "max-w-[min(48rem,100%)] rounded-[6px] border px-4 py-3 text-sm leading-6 shadow-none",
          isUser ? "bg-primary text-primary-foreground" : "bg-background",
          isSystem && "border-primary/25 bg-primary/8 text-foreground",
        )}
      >
        {message.meta ? <p className={cn("mb-1 text-xs", isUser ? "text-primary-foreground/75" : "text-muted-foreground")}>{message.meta}</p> : null}
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
      {isUser ? (
        <div className="grid size-8 shrink-0 place-items-center rounded-md border bg-primary text-primary-foreground">
          <Icon className="size-4" />
        </div>
      ) : null}
    </div>
  );
}

function AgentThinking() {
  return (
    <div className="flex gap-3">
      <div className="grid size-8 shrink-0 place-items-center rounded-md border bg-muted text-primary">
        <Loader2 className="size-4 animate-spin" />
      </div>
      <div className="rounded-[6px] border bg-background/55 px-4 py-3 text-sm text-muted-foreground shadow-none">
        正在检索资料、整理上下文并等待任务事件...
      </div>
    </div>
  );
}
