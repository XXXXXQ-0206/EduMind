import { useMemo, useState } from "react";
import { Play, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { Alert, Progress } from "@/components/ui/feedback";
import { Badge } from "@/components/ui/badge";
import { api, subscribeTaskEvents, type RagSearchResponse } from "@/lib/api";
import { workflowByKind, type FeatureKind } from "@/config/navigation";
import { useWorkspaceStore } from "@/stores/workspace-store";
import { useTaskStore } from "@/stores/task-store";

export function GenerationConsole({ kind }: { kind: FeatureKind }) {
  const workflow = workflowByKind(kind);
  const { role, selectedMaterialIds } = useWorkspaceStore();
  const { current, start, push } = useTaskStore();
  const [prompt, setPrompt] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);
  const [busy, setBusy] = useState(false);
  const [rag, setRag] = useState<RagSearchResponse | null>(null);
  const [error, setError] = useState("");

  const progress = useMemo(() => {
    if (!current) return 0;
    if (current.status === "done") return 100;
    if (current.phase === "ready") return 20;
    if (current.phase === "generating") return 55;
    if (current.phase === "packaging") return 80;
    return 35;
  }, [current]);

  async function runRag() {
    if (!prompt.trim()) return;
    setError("");
    setBusy(true);
    try {
      const result = await api.ragSearch(prompt, role, selectedMaterialIds);
      setRag(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG 检索失败");
    } finally {
      setBusy(false);
    }
  }

  async function runWorkflow() {
    if (!prompt.trim()) {
      setError("请先填写主题或问题。");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const includeMaterials = selectedMaterialIds.length > 0;
      const base = { includeMaterials, materialIds: selectedMaterialIds, role, topic: prompt, q: prompt };
      const payload =
        kind === "quiz"
          ? { ...base, count, difficulty }
          : kind === "paper"
            ? { ...base, difficulty, count_choice: 10, count_fill: 5, count_application: 2 }
            : kind === "slides"
              ? { ...base, pageCount: Math.max(5, count) }
              : base;
      const result = await api.startWorkflow(kind, payload);
      const taskId = String(result.chatId || result.quizId || result.paperId || result.noteId || result.pid || result.slideId || result.lessonPlanId || Date.now());
      start(kind, taskId);
      if (result.events) {
        subscribeTaskEvents(String(result.events), push, (err) => setError(err.message));
      } else {
        push({ type: "done", result });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务启动失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <workflow.icon className="h-5 w-5 text-primary" aria-hidden="true" />
            <CardTitle>{workflow.title}</CardTitle>
            <Badge variant={workflow.role === "teacher" ? "info" : "success"}>{workflow.role === "teacher" ? "教师工作流" : "学生工作流"}</Badge>
          </div>
          <CardDescription>{workflow.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Field label={workflow.promptLabel} hint="会优先使用资料篮中的多文件 RAG 上下文。">
            <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder={workflow.promptPlaceholder} />
          </Field>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="难度">
              <Select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                <option value="easy">简单</option>
                <option value="medium">中等</option>
                <option value="hard">困难</option>
              </Select>
            </Field>
            <Field label={kind === "slides" ? "页数 / 数量" : "题目数量"}>
              <Input type="number" min={1} max={25} value={count} onChange={(event) => setCount(Number(event.target.value))} />
            </Field>
          </div>
          {error ? <Alert title="操作失败" variant="destructive">{error}</Alert> : null}
          <div className="flex flex-wrap gap-2">
            <Button onClick={runWorkflow} loading={busy}>
              <Play className="h-4 w-4" />
              启动生成
            </Button>
            <Button type="button" variant="outline" onClick={runRag} loading={busy}>
              <Search className="h-4 w-4" />
              先检索 RAG
            </Button>
          </div>
        </CardContent>
      </Card>
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>任务进度</CardTitle>
            <CardDescription>SSE 优先，兼容后端现有 WebSocket URL。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={progress} label={current ? `${current.kind} / ${current.phase}` : "等待任务"} />
            <div className="max-h-48 overflow-auto rounded-md border bg-muted/40 p-3 text-xs leading-6">
              {current?.events.length ? current.events.map((event, index) => <p key={index}>{JSON.stringify(event)}</p>) : "暂无事件"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>RAG 摘要</CardTitle>
            <CardDescription>展示多文件检索结果和失败文件。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6">
            {rag ? (
              <>
                <div className="max-h-56 overflow-auto rounded-md border bg-background p-3 whitespace-pre-wrap">{rag.context || "未检索到上下文。"}</div>
                <p className="text-xs text-muted-foreground">
                  chunks: {rag.chunks.length} / files: {rag.files.length} / failed: {rag.failedFiles.length}
                </p>
              </>
            ) : (
              <p className="text-muted-foreground">点击“先检索 RAG”可在调用 agent 前检查多文件上下文。</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
