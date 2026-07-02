import { Link } from "react-router-dom";
import {
  BookOpenCheck,
  BrainCircuit,
  ChevronRight,
  Files,
  GraduationCap,
  Radio,
  Sparkles,
  SquarePen,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { workflowDefinitions } from "@/config/navigation";
import { useWorkspaceStore } from "@/stores/workspace-store";

export function DashboardPage() {
  const { role, setRole, files, selectedMaterialIds } = useWorkspaceStore();
  const workflows = workflowDefinitions.filter((item) => item.role === role);

  return (
    <div className="space-y-5">
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="border-y bg-transparent px-1 py-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0">
              <Badge variant="outline">React + shadcn/ui 新工作台</Badge>
              <h1 className="mt-3 max-w-4xl text-2xl font-semibold tracking-normal md:text-3xl">
                EduMind 把资料、Agent 对话和生成任务放进同一个操作台
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
                当前版本保留旧前端的信息架构：角色入口、侧边导航、资料文件夹、历史记录和功能工作流；视觉系统由 shadcn/Radix/Tailwind 重新实现。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link className={buttonVariants({ variant: "default" })} to="/workspace/chat">
                <BrainCircuit className="size-4" />
                打开对话
              </Link>
              <Link className={buttonVariants({ variant: "outline" })} to="/files">
                <Files className="size-4" />
                文件库
              </Link>
            </div>
          </div>
        </div>

        <Card className="gap-4">
          <CardHeader>
            <CardTitle className="text-base">当前上下文</CardTitle>
            <CardDescription>角色和资料会影响所有 Agent 调用。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setRole("student")}
                className={cn(roleCardClass(role === "student"))}
              >
                <GraduationCap className="size-4" />
                学生端
              </button>
              <button
                type="button"
                onClick={() => setRole("teacher")}
                className={cn(roleCardClass(role === "teacher"))}
              >
                <SquarePen className="size-4" />
                教师端
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <MiniMetric label="文件" value={files.length} />
              <MiniMetric label="资料夹" value={selectedMaterialIds.length} />
            </div>
          </CardContent>
        </Card>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="当前文件" value={files.length} detail="来自当前角色文件库" icon={Files} />
        <MetricCard label="资料文件夹" value={selectedMaterialIds.length} detail="进入 RAG 上下文" icon={Sparkles} tone="accent" />
        <MetricCard label="可用工作流" value={workflows.length} detail={role === "teacher" ? "教师生成入口" : "学生学习入口"} icon={BookOpenCheck} />
        <MetricCard label="任务通道" value="SSE" detail="保留 WebSocket 兼容" icon={Radio} tone="muted" />
      </div>

      <Tabs defaultValue="workflows" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workflows">功能入口</TabsTrigger>
          <TabsTrigger value="project">项目说明</TabsTrigger>
        </TabsList>
        <TabsContent value="workflows">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {workflows.map((workflow) => (
              <Card key={workflow.kind} className="transition-colors hover:border-primary/35">
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div className="grid size-10 place-items-center rounded-[6px] border bg-muted/35 text-primary">
                      <workflow.icon className="size-5" />
                    </div>
                    <Badge variant={workflow.role === "teacher" ? "info" : "secondary"}>{workflow.role === "teacher" ? "教师" : "学生"}</Badge>
                  </div>
                  <CardTitle>{workflow.title}</CardTitle>
                  <CardDescription>{workflow.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Link className={buttonVariants({ variant: "outline", className: "w-full justify-between" })} to={`/workspace/${workflow.kind}`}>
                    打开 Agent
                    <ChevronRight className="size-4" />
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="project">
          <div className="grid gap-4 lg:grid-cols-3">
            <InfoPanel title="项目介绍">
              EduMind 面向备课、授课、学习和复盘场景，提供多文件资料管理、RAG 检索、Agent 对话和生成式学习工具。
            </InfoPanel>
            <InfoPanel title="项目技术">
              前端采用 React、shadcn/ui、Radix UI 与 Tailwind CSS；后端微服务负责认证、文件、RAG、生成任务和记录管理。
            </InfoPanel>
            <InfoPanel title="协作入口">
              旧 Vue 前端保留在 frontend-legacy，新 React 前端保留旧布局并重写设计系统，可通过独立启动脚本验证。
            </InfoPanel>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function roleCardClass(active: boolean) {
  return cn(
    "flex min-h-16 items-center justify-center gap-2 rounded-[6px] border p-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    active ? "border-primary/50 bg-primary/10 text-primary" : "bg-muted/30 text-muted-foreground hover:bg-muted hover:text-foreground",
  );
}

function MiniMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-[6px] border bg-muted/25 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "primary",
}: {
  label: string;
  value: number | string;
  detail: string;
  icon: typeof Files;
  tone?: "primary" | "accent" | "muted";
}) {
  return (
    <Card className="gap-4">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardDescription>{label}</CardDescription>
            <CardTitle className="mt-2 text-3xl tabular-nums">{value}</CardTitle>
          </div>
          <div
            className={cn(
              "grid size-10 place-items-center rounded-[6px] border",
              tone === "accent" && "bg-accent/15 text-accent",
              tone === "primary" && "bg-primary/10 text-primary",
              tone === "muted" && "bg-muted text-muted-foreground",
            )}
          >
            <Icon className="size-5" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{detail}</CardContent>
    </Card>
  );
}

function InfoPanel({ title, children }: { title: string; children: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-6 text-muted-foreground">{children}</CardContent>
    </Card>
  );
}
