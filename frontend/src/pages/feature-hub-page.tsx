import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  BrainCircuit,
  Clapperboard,
  FileQuestion,
  Mic2,
  RefreshCw,
  Search,
  Sparkles,
  StickyNote,
} from "lucide-react";
import { AgentConversationPanel, type AgentMessage } from "@/components/patterns/agent-conversation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, type ExamRecord, type FlashcardDeck, type SpeakingRecord, type VideoRecord, type WrongbookSummary } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";

type FeatureType = "tools" | "wrongbook" | "records" | "cards" | "exam" | "video" | "speaking" | "bilibili" | "planner";

type FeatureConfig = {
  type: FeatureType;
  title: string;
  desc: string;
  role: "student" | "teacher" | "both";
  endpoints: string[];
  links: Array<{ label: string; to: string }>;
};

const featureMap: Record<string, FeatureConfig> = {
  "/tools": {
    type: "tools",
    title: "工具集",
    desc: "集中进入学习、备课和资料处理工具。",
    role: "both",
    endpoints: ["/files", "/chats", "/quizzes"],
    links: [
      { label: "文件库", to: "/files" },
      { label: "资料问答", to: "/workspace/chat" },
      { label: "生成记录", to: "/records" },
    ],
  },
  "/wrong-book": {
    type: "wrongbook",
    title: "错题本",
    desc: "基于测验作答记录汇总错题、薄弱点和掌握趋势。",
    role: "student",
    endpoints: ["/wrongbook/summary", "/wrongbook/report", "/wrongbook/weak-points"],
    links: [{ label: "生成测验", to: "/workspace/quiz" }],
  },
  "/wrong-book/practice": {
    type: "wrongbook",
    title: "错题练习",
    desc: "从错题本汇总中回到练习任务，继续巩固薄弱知识点。",
    role: "student",
    endpoints: ["/wrongbook/summary", "/quiz"],
    links: [{ label: "生成新练习", to: "/workspace/quiz" }],
  },
  "/learning-records": {
    type: "records",
    title: "学习记录",
    desc: "学生侧学习历史统一入口。",
    role: "student",
    endpoints: ["/chats?role=student", "/quizzes", "/wrongbook/summary"],
    links: [{ label: "查看生成记录", to: "/records" }],
  },
  "/teaching-records": {
    type: "records",
    title: "教学记录",
    desc: "教师侧试卷、教案、课件和教学内容历史入口。",
    role: "teacher",
    endpoints: ["/papers", "/lesson-plans", "/slides", "/teaching-videos"],
    links: [{ label: "查看生成记录", to: "/records" }],
  },
  "/cards": {
    type: "cards",
    title: "学习袋",
    desc: "管理基础问答闪卡和知识卡片。",
    role: "student",
    endpoints: ["/flashcards", "/flashcards/decks"],
    links: [{ label: "资料问答", to: "/workspace/chat" }],
  },
  "/knowledge-cards": {
    type: "cards",
    title: "知识卡片",
    desc: "从资料或错题中生成结构化知识点卡片。",
    role: "student",
    endpoints: ["/flashcards/decks"],
    links: [{ label: "智能笔记", to: "/workspace/smartnotes" }],
  },
  "/exam": {
    type: "exam",
    title: "考试训练",
    desc: "创建综合考试任务并通过事件通道跟踪生成进度。",
    role: "student",
    endpoints: ["/exams", "/exam"],
    links: [{ label: "自测练习", to: "/workspace/quiz" }],
  },
  "/teaching-video": {
    type: "video",
    title: "教学视频",
    desc: "教师侧视频生成任务入口，支持历史视频查看。",
    role: "teacher",
    endpoints: ["/teaching-video", "/teaching-videos"],
    links: [{ label: "课件生成", to: "/workspace/slides" }],
  },
  "/english-speaking": {
    type: "speaking",
    title: "英语口语",
    desc: "口语素材生成、音频上传和评测历史入口。",
    role: "student",
    endpoints: ["/speaking/generate", "/speaking/upload", "/speaking/evaluate", "/speaking/history"],
    links: [{ label: "学习记录", to: "/records" }],
  },
  "/bili-learning": {
    type: "bilibili",
    title: "B站学习",
    desc: "通过 Bilibili Bridge 检索学习视频。",
    role: "student",
    endpoints: ["/api/bilibili/search"],
    links: [{ label: "文件库", to: "/files" }],
  },
  "/teacher/bili-learning": {
    type: "bilibili",
    title: "B站备课",
    desc: "教师侧视频备课检索入口。",
    role: "teacher",
    endpoints: ["/api/bilibili/search"],
    links: [{ label: "教案生成", to: "/workspace/lesson-plan" }],
  },
  "/planner": {
    type: "planner",
    title: "学习规划",
    desc: "任务清单、周计划和资料关联入口。",
    role: "student",
    endpoints: ["/tasks", "/planner/weekly"],
    links: [{ label: "资料问答", to: "/workspace/chat" }],
  },
};

type FeatureData = {
  wrongbook?: WrongbookSummary;
  decks?: FlashcardDeck[];
  cards?: Array<Record<string, unknown>>;
  speaking?: SpeakingRecord[];
  videos?: VideoRecord[];
  exams?: ExamRecord[];
  records?: Array<Record<string, unknown>>;
  bilibili?: Array<Record<string, unknown>>;
};

export function FeatureHubPage() {
  const location = useLocation();
  const config = featureMap[location.pathname] ?? featureMap["/tools"];
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<FeatureData>({});
  const [raw, setRaw] = useState<unknown>(null);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<AgentMessage[]>([]);

  const Icon = useMemo(() => iconFor(config.type), [config.type]);

  async function load(searchTerm = "数学") {
    setBusy(true);
    setError("");
    try {
      if (config.type === "wrongbook") {
        const wrongbook = await api.wrongbookSummary();
        setData({ wrongbook });
        setRaw(wrongbook);
      } else if (config.type === "cards") {
        const [cards, decks] = await Promise.allSettled([api.listFlashcards(), api.listFlashcardDecks()]);
        const next = {
          cards: cards.status === "fulfilled" ? cards.value.cards ?? [] : [],
          decks: decks.status === "fulfilled" ? decks.value.decks ?? [] : [],
        };
        setData(next);
        setRaw(next);
      } else if (config.type === "speaking") {
        const result = await api.listSpeakingHistory();
        const speaking = result.history ?? result.records ?? [];
        setData({ speaking });
        setRaw(result);
      } else if (config.type === "video") {
        const result = await api.listTeachingVideos();
        setData({ videos: result.videos ?? [] });
        setRaw(result);
      } else if (config.type === "exam") {
        const result = await api.listExams();
        setData({ exams: result.exams ?? [] });
        setRaw(result);
      } else if (config.type === "bilibili") {
        const result = await api.searchBilibili(searchTerm);
        const bilibili = result.items ?? result.results ?? [];
        setData({ bilibili });
        setRaw(result);
      } else {
        const results = await Promise.allSettled(config.endpoints.map((endpoint) => api.getJson<Record<string, unknown>>(endpoint)));
        const records = results.map((result, index) => ({
          endpoint: config.endpoints[index],
          status: result.status,
          value: result.status === "fulfilled" ? result.value : { error: result.reason instanceof Error ? result.reason.message : "failed" },
        }));
        setData({ records });
        setRaw(records);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    setMessages([]);
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  if (config.type === "bilibili") {
    async function searchVideos(text: string) {
      setMessages((items) => [...items, { id: `u-${Date.now()}`, role: "user", content: text, meta: config.role === "teacher" ? "备课检索" : "学习检索" }]);
      await load(text);
      setMessages((items) => [
        ...items,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: `已完成视频检索。当前结果会在下方更新，可继续换关键词追问。\n关键词：${text}`,
          meta: "Bilibili Bridge",
        },
      ]);
    }

    return (
      <AgentConversationPanel
        title={config.title}
        description={config.desc}
        eyebrow={config.role === "teacher" ? "教师视频备课" : "学生视频学习"}
        placeholder="输入视频检索关键词，例如：函数极限、牛顿第二定律、唐宋诗词..."
        messages={messages}
        quickPrompts={[
          { label: "数学复习", value: "初中函数图像讲解" },
          { label: "课堂导入", value: "物理牛顿运动定律课堂导入视频" },
          { label: "知识串讲", value: "高中语文古诗词意象分析" },
        ]}
        busy={busy}
        progress={busy ? 45 : data.bilibili ? 100 : 0}
        progressLabel={busy ? "正在检索" : "检索完成"}
        onSubmit={searchVideos}
        side={<FeatureSide config={config} Icon={Icon} onRefresh={() => void load()} busy={busy} />}
        result={<BilibiliPanel rows={data.bilibili ?? []} />}
      />
    );
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <Icon className="size-5 text-primary" />
                <CardTitle>{config.title}</CardTitle>
                <Badge variant={config.role === "teacher" ? "info" : config.role === "student" ? "secondary" : "outline"}>
                  {config.role === "teacher" ? "教师端" : config.role === "student" ? "学生端" : "通用"}
                </Badge>
              </div>
              <CardDescription className="mt-2">{config.desc}</CardDescription>
            </div>
            <Button variant="outline" onClick={() => void load()} loading={busy}>
              <RefreshCw className="size-4" />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {config.links.map((link) => (
              <Link key={link.to} className={buttonVariants({ variant: "outline" })} to={link.to}>
                {link.label}
                <ArrowRight className="size-4" />
              </Link>
            ))}
          </div>
          <EndpointChips endpoints={config.endpoints} />
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>加载失败</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      {busy ? <LoadingRows /> : <FeatureBody config={config} data={data} raw={raw} />}
    </div>
  );
}

function FeatureSide({ config, Icon, onRefresh, busy }: { config: FeatureConfig; Icon: ReturnType<typeof iconFor>; onRefresh: () => void; busy: boolean }) {
  return (
    <Card className="gap-4">
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Icon className="size-4 text-primary" />
          {config.title}
        </CardTitle>
        <CardDescription>{config.desc}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button variant="outline" size="sm" className="w-full" onClick={onRefresh} loading={busy}>
          <RefreshCw className="size-4" />
          刷新结果
        </Button>
        <EndpointChips endpoints={config.endpoints} compact />
      </CardContent>
    </Card>
  );
}

function FeatureBody({ config, data, raw }: { config: FeatureConfig; data: FeatureData; raw: unknown }) {
  if (config.type === "wrongbook") return <WrongbookPanel summary={data.wrongbook} />;
  if (config.type === "cards") return <CardsPanel decks={data.decks ?? []} cards={data.cards ?? []} />;
  if (config.type === "speaking") return <SimpleRecordPanel title="口语历史" rows={data.speaking ?? []} empty="暂无口语记录。" />;
  if (config.type === "video") return <SimpleRecordPanel title="教学视频历史" rows={data.videos ?? []} empty="暂无教学视频。" />;
  if (config.type === "exam") return <SimpleRecordPanel title="考试记录" rows={data.exams ?? []} empty="暂无考试记录。" />;
  return <RawPanel raw={raw} />;
}

function WrongbookPanel({ summary }: { summary?: WrongbookSummary }) {
  const stats = summary?.stats ?? {};
  const weakTopics = summary?.weakTopics ?? [];
  const wrongQuestions = summary?.wrongQuestions ?? [];
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <Card>
        <CardHeader>
          <CardTitle>错题概览</CardTitle>
          <CardDescription>来自错题汇总的结构化学习反馈。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <Stat label="错题数" value={stats.wrongCount ?? 0} />
          <Stat label="掌握数" value={stats.masteredCount ?? 0} />
          <Stat label="掌握率" value={`${stats.masteryRate ?? 0}%`} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>薄弱点</CardTitle>
          <CardDescription>按错误率与次数排序。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {weakTopics.length ? weakTopics.slice(0, 6).map((topic, index) => (
            <div key={`${String(topic.name)}-${index}`} className="rounded-lg border bg-muted/20 p-3">
              <p className="font-medium">{String(topic.name ?? "未命名知识点")}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{String(topic.suggestion ?? "继续巩固。")}</p>
            </div>
          )) : <p className="text-sm text-muted-foreground">暂无薄弱点。</p>}
        </CardContent>
      </Card>
      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle>近期错题</CardTitle>
          <CardDescription>用于回到测验工作流继续练习。</CardDescription>
        </CardHeader>
        <CardContent>
          <RecordTable rows={wrongQuestions.slice(0, 8)} empty="暂无错题记录。" />
        </CardContent>
      </Card>
    </div>
  );
}

function CardsPanel({ decks, cards }: { decks: FlashcardDeck[]; cards: Array<Record<string, unknown>> }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <Card>
        <CardHeader>
          <CardTitle>卡组</CardTitle>
          <CardDescription>知识卡片和闪卡集合。</CardDescription>
        </CardHeader>
        <CardContent>
          <RecordTable rows={decks} empty="暂无卡组。" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>卡片统计</CardTitle>
          <CardDescription>用于快速判断学习袋内容。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Stat label="卡组数" value={decks.length} />
          <Stat label="散卡数" value={cards.length} />
        </CardContent>
      </Card>
    </div>
  );
}

function BilibiliPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  return (
    <Card className="mt-2">
      <CardHeader>
        <CardTitle>视频检索结果</CardTitle>
        <CardDescription>通过 Bilibili Bridge 返回的候选视频。</CardDescription>
      </CardHeader>
      <CardContent>
        <RecordTable rows={rows} empty="暂无视频结果。" />
      </CardContent>
    </Card>
  );
}

function SimpleRecordPanel({ title, rows, empty }: { title: string; rows: Array<Record<string, unknown>>; empty: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>保留历史 URL 的同时使用新 React 数据表呈现。</CardDescription>
      </CardHeader>
      <CardContent>
        <RecordTable rows={rows} empty={empty} />
      </CardContent>
    </Card>
  );
}

function RawPanel({ raw }: { raw: unknown }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>接口状态</CardTitle>
        <CardDescription>多个服务端点的聚合结果。</CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="max-h-96 overflow-auto rounded-lg border bg-background p-3 text-xs leading-5">
          {JSON.stringify(raw ?? [], null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}

function RecordTable({ rows, empty }: { rows: Array<Record<string, unknown>>; empty: string }) {
  if (!rows.length) return <p className="py-8 text-center text-sm text-muted-foreground">{empty}</p>;
  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>名称</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>时间</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={String(row.id ?? row.title ?? row.name ?? index)}>
              <TableCell className="max-w-96 truncate font-medium">{String(row.title ?? row.name ?? row.question ?? row.id ?? "未命名")}</TableCell>
              <TableCell><Badge variant={row.error ? "destructive" : "outline"}>{String(row.status ?? row.level ?? row.tag ?? "saved")}</Badge></TableCell>
              <TableCell>{formatDate((row.updated_at ?? row.created_at ?? row.at ?? row.time) as string | number | undefined)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function EndpointChips({ endpoints, compact = false }: { endpoints: string[]; compact?: boolean }) {
  return (
    <div className={cn("rounded-lg border bg-muted/25 p-3", compact && "p-2")}>
      {!compact ? <p className="mb-2 text-sm font-medium">相关 API</p> : null}
      <div className="flex flex-wrap gap-2">
        {endpoints.map((endpoint) => <Badge key={endpoint} variant="outline">{endpoint}</Badge>)}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function LoadingRows() {
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </CardContent>
    </Card>
  );
}

function iconFor(type: FeatureType) {
  const icons = {
    tools: Activity,
    wrongbook: BookOpenCheck,
    records: StickyNote,
    cards: Sparkles,
    exam: FileQuestion,
    video: Clapperboard,
    speaking: Mic2,
    bilibili: Search,
    planner: BrainCircuit,
  };
  return icons[type];
}
