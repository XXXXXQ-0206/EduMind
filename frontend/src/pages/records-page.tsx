import { useEffect, useMemo, useState } from "react";
import { ClipboardList, MessageSquareText, RefreshCw, Search } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type RecordItem } from "@/lib/api";
import { formatDate } from "@/lib/utils";

type Row = RecordItem & { category: string };

export function RecordsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const result = await api.listRecords();
      const next: Row[] = [];
      if (result.chats.status === "fulfilled") next.push(...result.chats.value.chats.map((item) => ({ ...item, category: "聊天" })));
      if (result.quizzes.status === "fulfilled") next.push(...result.quizzes.value.quizzes.map((item) => ({ ...item, category: "测验" })));
      if (result.papers.status === "fulfilled") next.push(...result.papers.value.papers.map((item) => ({ ...item, category: "试卷" })));
      if (result.lessonPlans.status === "fulfilled") next.push(...result.lessonPlans.value.lessonPlans.map((item) => ({ ...item, category: "教案" })));
      if (result.slides.status === "fulfilled") next.push(...result.slides.value.slides.map((item) => ({ ...item, category: "课件" })));
      setRows(next.sort((a, b) => String(b.updated_at || b.created_at || b.at || "").localeCompare(String(a.updated_at || a.created_at || a.at || ""))));
    } catch (err) {
      setError(err instanceof Error ? err.message : "记录加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<string, number>();
    rows.forEach((row) => map.set(row.category, (map.get(row.category) || 0) + 1));
    return Array.from(map.entries());
  }, [rows]);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesCategory = category === "all" || row.category === category;
      const text = `${row.title || ""} ${row.id || ""} ${row.status || ""} ${row.category}`.toLowerCase();
      return matchesCategory && (!keyword || text.includes(keyword));
    });
  }, [rows, query, category]);

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
            <div>
              <CardTitle>生成记录</CardTitle>
              <CardDescription>统一查看聊天、测验、试卷、教案和课件历史，保留旧前端记录入口的归档关系。</CardDescription>
            </div>
            <Button variant="outline" onClick={() => void load()} loading={loading}>
              <RefreshCw className="size-4" />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>记录加载失败</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
              <Input value={query} onChange={(event) => setQuery(event.target.value)} className="pl-9" placeholder="搜索标题、状态或记录 ID" />
            </div>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {grouped.map(([name]) => <SelectItem key={name} value={name}>{name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <Tabs defaultValue="table" className="space-y-4">
            <TabsList>
              <TabsTrigger value="table">记录表</TabsTrigger>
              <TabsTrigger value="summary">分类统计</TabsTrigger>
            </TabsList>
            <TabsContent value="table">
              <div className="overflow-hidden rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>类型</TableHead>
                      <TableHead>标题</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>更新时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.length ? filtered.map((row) => (
                      <TableRow key={`${row.category}-${row.id}`}>
                        <TableCell>
                          <span className="inline-flex items-center gap-2">
                            {row.category === "聊天" ? <MessageSquareText className="size-4" /> : <ClipboardList className="size-4" />}
                            {row.category}
                          </span>
                        </TableCell>
                        <TableCell className="max-w-96 truncate font-medium">{row.title || row.id}</TableCell>
                        <TableCell>
                          <Badge variant={row.error ? "destructive" : row.status === "ready" ? "success" : "outline"}>
                            {row.error ? "error" : row.status || "saved"}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatDate(row.updated_at || row.created_at || row.at)}</TableCell>
                      </TableRow>
                    )) : (
                      <TableRow>
                        <TableCell colSpan={4} className="h-32 text-center text-muted-foreground">暂无生成记录。</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
            <TabsContent value="summary">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                {grouped.length ? grouped.map(([name, count]) => (
                  <div key={name} className="rounded-lg border bg-muted/25 p-4">
                    <p className="text-sm text-muted-foreground">{name}</p>
                    <p className="mt-2 text-3xl font-semibold tabular-nums">{count}</p>
                  </div>
                )) : <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">暂无记录</div>}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
