import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import {
  Download,
  Eye,
  FileArchive,
  FileText,
  FolderOpen,
  RefreshCw,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { MaterialPicker } from "@/components/patterns/material-picker";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { api, type LibraryFile, type RagSearchResponse } from "@/lib/api";
import { cn, formatBytes, formatDate } from "@/lib/utils";
import { useWorkspaceStore } from "@/stores/workspace-store";

const typeOptions = [
  { key: "all", label: "全部" },
  { key: "pdf", label: "PDF" },
  { key: "doc", label: "DOC" },
  { key: "ppt", label: "PPT" },
  { key: "text", label: "文本" },
  { key: "image", label: "图片" },
  { key: "audio", label: "音频" },
  { key: "video", label: "视频" },
  { key: "other", label: "其他" },
];

export function FileLibraryPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { role, files, setFiles, selectedMaterialIds, toggleMaterial, clearMaterials } = useWorkspaceStore();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [ragQuery, setRagQuery] = useState("");
  const [rag, setRag] = useState<RagSearchResponse | null>(null);
  const [preview, setPreview] = useState<LibraryFile | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.listFiles(role);
      setFiles(result.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件列表加载失败");
    } finally {
      setLoading(false);
    }
  }, [role, setFiles]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return files.filter((file) => {
      const kind = fileKind(file);
      const name = `${file.originalName} ${file.filename} ${file.mimeType}`.toLowerCase();
      return (!keyword || name.includes(keyword)) && (typeFilter === "all" || kind === typeFilter);
    });
  }, [files, query, typeFilter]);

  const stats = useMemo(() => {
    const ready = files.filter((file) => file.ragStatus === "ready").length;
    const latest = [...files].sort((a, b) => (b.uploadedAt || 0) - (a.uploadedAt || 0))[0];
    return {
      count: files.length,
      size: formatBytes(files.reduce((sum, file) => sum + (file.size || 0), 0)),
      ready,
      latest,
    };
  }, [files]);

  async function uploadFiles(next: File[]) {
    if (!next.length || uploading) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadFiles(next, role);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败，请检查文件后重试");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    await uploadFiles(Array.from(event.target.files || []));
  }

  async function remove(file: LibraryFile) {
    setError("");
    try {
      await api.deleteFile(file.id, role);
      setFiles(files.filter((item) => item.id !== file.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  async function rebuild(file: LibraryFile) {
    setError("");
    try {
      await api.rebuildFileIndex(file.id, role);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "索引重建失败");
    }
  }

  async function searchRag() {
    if (!ragQuery.trim()) return;
    setError("");
    try {
      const result = await api.ragSearch(ragQuery, role, selectedMaterialIds);
      setRag(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG 检索失败");
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    void uploadFiles(Array.from(event.dataTransfer.files || []));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">{role === "teacher" ? "教师资料" : "学习资料"}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-normal">{role === "teacher" ? "教师文件库" : "文件库"}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            上传资料后会进入多文件 RAG 索引。文件库布局保留上传区、交互文件夹、搜索列表和预览入口。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void load()} loading={loading}>
            <RefreshCw className="size-4" />
            刷新
          </Button>
          <Button onClick={() => inputRef.current?.click()} loading={uploading}>
            <Upload className="size-4" />
            上传文件
          </Button>
        </div>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>文件库操作失败</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="size-5 text-primary" />
                上传文件
              </CardTitle>
              <CardDescription>{role === "teacher" ? "上传课程资料、教案、课件与试卷素材。" : "上传 PDF、Office、文本、图片或音频作为学习资料。"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className={cn(
                  "rounded-lg border border-dashed bg-muted/25 p-5 transition-colors",
                  dragActive && "border-primary bg-primary/8",
                )}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={onDrop}
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                  <div className="grid size-12 shrink-0 place-items-center rounded-lg border bg-background text-primary">
                    <Upload className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">拖拽文件到这里，或点击选择</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">支持 PDF、PPT、DOC、TXT、MD、图片与音频；上传后后端会建立 RAG 索引。</p>
                  </div>
                  <Button variant="outline" onClick={() => inputRef.current?.click()} loading={uploading}>
                    选择文件
                  </Button>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-4">
                <StatTile label="文件数量" value={stats.count} />
                <StatTile label="总容量" value={stats.size} />
                <StatTile label="RAG 就绪" value={`${stats.ready}/${stats.count}`} />
                <StatTile label="最近上传" value={stats.latest ? formatDate(stats.latest.uploadedAt) : "暂无"} title={stats.latest?.originalName} />
              </div>

              <MaterialPicker
                files={files}
                selectedIds={selectedMaterialIds}
                onToggle={toggleMaterial}
                onClear={clearMaterials}
                label={role === "teacher" ? "教学交互文件夹" : "学习交互文件夹"}
                hint="这里对应旧前端上传框内的交互文件夹，所选文件会进入 Agent 的 RAG 上下文。"
                compact
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="size-5 text-primary" />
                    搜索文件
                  </CardTitle>
                  <CardDescription>按文件名、扩展名和 RAG 状态管理资料。</CardDescription>
                </div>
                <Badge variant="outline">{filtered.length} 个匹配文件</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem]">
                <div className="grid gap-2">
                  <Label htmlFor="file-query">文件名或类型</Label>
                  <Input id="file-query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入关键词筛选..." />
                </div>
                <div className="grid gap-2">
                  <Label>类型</Label>
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {typeOptions.map((option) => (
                        <SelectItem key={option.key} value={option.key}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="overflow-hidden rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>文件</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>大小</TableHead>
                      <TableHead>时间</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.length ? (
                      filtered.map((file) => (
                        <TableRow key={file.id}>
                          <TableCell className="max-w-[22rem]">
                            <div className="flex items-center gap-3">
                              <div className="grid size-9 shrink-0 place-items-center rounded-md border bg-muted/40">
                                <FileText className="size-4 text-muted-foreground" />
                              </div>
                              <div className="min-w-0">
                                <button type="button" className="block truncate font-medium hover:text-primary" onClick={() => setPreview(file)}>
                                  {file.originalName || file.filename}
                                </button>
                                <p className="truncate text-xs text-muted-foreground">{file.mimeType || fileKind(file)}</p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={file.ragStatus === "ready" ? "success" : file.ragStatus === "error" ? "destructive" : "warning"}>
                              {ragStatusLabel(file)}
                            </Badge>
                            <p className="mt-1 text-xs text-muted-foreground">{file.ragChunkCount ?? 0} chunks</p>
                          </TableCell>
                          <TableCell>{formatBytes(file.size)}</TableCell>
                          <TableCell>{formatDate(file.uploadedAt)}</TableCell>
                          <TableCell>
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="icon-sm" onClick={() => setPreview(file)} aria-label="预览文件">
                                <Eye className="size-4" />
                              </Button>
                              <Button variant="ghost" size="icon-sm" onClick={() => void rebuild(file)} aria-label="重建索引">
                                <RefreshCw className="size-4" />
                              </Button>
                              <Button variant="ghost" size="icon-sm" onClick={() => void remove(file)} aria-label="删除文件">
                                <Trash2 className="size-4 text-destructive" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                          暂无文件。请先在上方上传资料。
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        <RagProbeCard
          query={ragQuery}
          result={rag}
          busy={loading}
          selectedCount={selectedMaterialIds.length}
          onQueryChange={setRagQuery}
          onSearch={() => void searchRag()}
        />
      </section>

      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        multiple
        accept=".pdf,.ppt,.pptx,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a"
        onChange={upload}
      />
      <PreviewSheet file={preview} onOpenChange={(open) => !open && setPreview(null)} />
    </div>
  );
}

function RagProbeCard({
  query,
  result,
  busy,
  selectedCount,
  onQueryChange,
  onSearch,
}: {
  query: string;
  result: RagSearchResponse | null;
  busy: boolean;
  selectedCount: number;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
}) {
  return (
    <Card className="h-fit xl:sticky xl:top-20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FolderOpen className="size-5 text-primary" />
          RAG 检索助手
        </CardTitle>
        <CardDescription>在调用 Agent 前，先用对话方式检查多文件上下文。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="向所选资料提问，例如：这些 PDF 的共同重点是什么？" />
        <Button className="w-full" onClick={onSearch} disabled={!query.trim()} loading={busy}>
          <Search className="size-4" />
          检索 {selectedCount} 个文件
        </Button>
        {result ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-md border bg-muted/30 p-2">
                <div className="font-semibold">{result.files.length}</div>
                <div className="text-muted-foreground">文件</div>
              </div>
              <div className="rounded-md border bg-muted/30 p-2">
                <div className="font-semibold">{result.chunks.length}</div>
                <div className="text-muted-foreground">片段</div>
              </div>
              <div className="rounded-md border bg-muted/30 p-2">
                <div className="font-semibold">{result.failedFiles.length}</div>
                <div className="text-muted-foreground">失败</div>
              </div>
            </div>
            <div className="max-h-96 overflow-auto rounded-lg border bg-background p-3 text-sm leading-6 whitespace-pre-wrap">
              {result.context || "没有检索到上下文。"}
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-dashed p-4 text-sm leading-6 text-muted-foreground">
            这个区域替代旧的调试输入框，保留文本输入能力，但呈现为 Agent 检索对话前置步骤。
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PreviewSheet({ file, onOpenChange }: { file: LibraryFile | null; onOpenChange: (open: boolean) => void }) {
  return (
    <Sheet open={Boolean(file)} onOpenChange={onOpenChange}>
      <SheetContent className="w-[min(54rem,92vw)] sm:max-w-none">
        {file ? (
          <>
            <SheetHeader>
              <SheetTitle>{file.originalName || file.filename}</SheetTitle>
              <SheetDescription>{fileKind(file)} · {formatBytes(file.size)}</SheetDescription>
            </SheetHeader>
            <div className="min-h-0 flex-1 overflow-auto px-4 pb-4">
              <div className="mb-3 flex justify-end">
                <Button variant="outline" size="sm" asChild>
                  <a href={file.url} target="_blank" rel="noreferrer">
                    <Download className="size-4" />
                    新窗口打开
                  </a>
                </Button>
              </div>
              <PreviewContent file={file} />
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

function PreviewContent({ file }: { file: LibraryFile }) {
  const type = previewType(file);
  if (type === "image") return <img src={file.url} alt={file.originalName} className="max-h-[72vh] w-full rounded-lg border object-contain" />;
  if (type === "audio") return <audio controls src={file.url} className="w-full" />;
  if (type === "pdf" || type === "text") return <iframe src={file.url} className="h-[72vh] w-full rounded-lg border" title="文件预览" />;
  return (
    <div className="grid min-h-80 place-items-center rounded-lg border border-dashed text-center text-sm text-muted-foreground">
      <div>
        <FileArchive className="mx-auto mb-3 size-8" />
        该文件类型暂不支持内嵌预览，请在新窗口打开。
      </div>
    </div>
  );
}

function StatTile({ label, value, title }: { label: string; value: string | number; title?: string }) {
  return (
    <div className="min-w-0 rounded-lg border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold tabular-nums" title={title || String(value)}>
        {value}
      </p>
    </div>
  );
}

function fileKind(file: LibraryFile) {
  const name = (file.originalName || file.filename || "").toLowerCase();
  const mime = file.mimeType || "";
  if (name.endsWith(".pdf")) return "pdf";
  if (name.endsWith(".ppt") || name.endsWith(".pptx")) return "ppt";
  if (name.endsWith(".doc") || name.endsWith(".docx")) return "doc";
  if (name.endsWith(".txt") || name.endsWith(".md")) return "text";
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.startsWith("video/")) return "video";
  return "other";
}

function previewType(file: LibraryFile) {
  const kind = fileKind(file);
  if (kind === "image" || kind === "audio" || kind === "pdf" || kind === "text") return kind;
  return "other";
}

function ragStatusLabel(file: LibraryFile) {
  const status = (file.ragStatus || "").toLowerCase();
  if (status === "ready") return file.ragChunkCount ? `RAG ${file.ragChunkCount}段` : "RAG 就绪";
  if (status === "empty") return "RAG 空";
  if (status === "error") return "RAG 错误";
  return status || file.ragVectorStatus || "pending";
}
