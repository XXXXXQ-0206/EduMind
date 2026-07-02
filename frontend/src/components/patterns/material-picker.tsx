import { CheckCircle2, FileText, FolderOpen, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollAreaShim } from "@/components/patterns/scroll-area-shim";
import type { LibraryFile } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

export function MaterialPicker({
  files,
  selectedIds,
  onToggle,
  onClear,
  label = "学习交互文件夹",
  hint = "勾选资料后，Agent 会在调用前执行多文件 RAG 检索。",
  compact = false,
}: {
  files: LibraryFile[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  onClear: () => void;
  label?: string;
  hint?: string;
  compact?: boolean;
}) {
  const [query, setQuery] = useState("");
  const selected = useMemo(() => files.filter((file) => selectedIds.includes(file.id)), [files, selectedIds]);
  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return files;
    return files.filter((file) => `${file.originalName} ${file.filename} ${file.mimeType}`.toLowerCase().includes(keyword));
  }, [files, query]);

  return (
    <div className={cn("rounded-[6px] border bg-card/80 shadow-none", compact && "text-sm")}>
      <div className="border-b p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="flex items-center gap-2 font-medium">
              <FolderOpen className="size-4 text-primary" />
              {label}
            </p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">{hint}</p>
          </div>
          <Badge variant={selected.length ? "info" : "outline"}>{selected.length}</Badge>
        </div>
        {selected.length ? (
          <div className="mt-3 space-y-2">
            {selected.slice(0, 3).map((file) => (
              <div key={file.id} className="flex items-center gap-2 rounded-md border bg-muted/30 px-2 py-1.5">
                <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1 truncate text-xs">{file.originalName || file.filename}</span>
                <Button variant="ghost" size="icon-xs" onClick={() => onToggle(file.id)} aria-label="移出资料">
                  <X className="size-3" />
                </Button>
              </div>
            ))}
            {selected.length > 3 ? <p className="text-xs text-muted-foreground">还有 {selected.length - 3} 个文件已选择</p> : null}
          </div>
        ) : null}
      </div>

      <div className="space-y-3 p-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} className="pl-8" placeholder="筛选文件" />
        </div>
        <ScrollAreaShim className={cn("max-h-72", compact && "max-h-52")}>
          {filtered.length ? (
            <div className="space-y-1 pr-1">
              {filtered.map((file) => {
                const checked = selectedIds.includes(file.id);
                return (
                  <button
                    key={file.id}
                    type="button"
                    aria-pressed={checked}
                    aria-label={`${checked ? "移出资料" : "加入资料"} ${file.originalName || file.filename}`}
                    onClick={() => onToggle(file.id)}
                    className={cn(
                      "flex w-full items-start gap-3 rounded-md border border-transparent p-2 text-left transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      checked && "border-primary/25 bg-primary/8",
                    )}
                  >
                    <span
                      aria-hidden="true"
                      className={cn(
                        "mt-0.5 grid size-4 shrink-0 place-items-center rounded-[4px] border border-input bg-background shadow-xs",
                        checked && "border-primary bg-primary text-primary-foreground",
                      )}
                    >
                      {checked ? <CheckCircle2 className="size-3" /> : null}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">{file.originalName || file.filename}</span>
                      <span className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <span>{formatBytes(file.size)}</span>
                        <Badge variant={file.ragStatus === "ready" ? "success" : file.ragStatus === "error" ? "destructive" : "warning"}>
                          {file.ragStatus || "pending"}
                        </Badge>
                      </span>
                    </span>
                    {checked ? <CheckCircle2 className="mt-0.5 size-4 text-primary" aria-hidden="true" /> : null}
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-md border border-dashed p-4 text-sm leading-6 text-muted-foreground">
              当前没有匹配文件。请先在文件库上传 PDF、Office 或文本资料。
            </div>
          )}
        </ScrollAreaShim>
        <Button variant="outline" size="sm" className="w-full" onClick={onClear} disabled={!selectedIds.length}>
          清空文件夹
        </Button>
      </div>
    </div>
  );
}
