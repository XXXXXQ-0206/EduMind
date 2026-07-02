import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  BrainCircuit,
  ChevronDown,
  LogOut,
  Moon,
  PanelLeft,
  Settings,
  Sparkles,
  Sun,
  UserRound,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { SegmentedControl } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { api, type ChatInfo } from "@/lib/api";
import { cn } from "@/lib/utils";
import { navSections, type NavItem, type Role } from "@/config/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useWorkspaceStore } from "@/stores/workspace-store";

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { user, status, restore, logout } = useAuthStore();
  const { role, setRole, files } = useWorkspaceStore();
  const [recentChats, setRecentChats] = useState<ChatInfo[]>([]);

  useEffect(() => {
    void restore();
  }, [restore]);

  useEffect(() => {
    const queryRole = searchParams.get("role");
    if (queryRole === "teacher" || queryRole === "student") setRole(queryRole);
  }, [searchParams, setRole]);

  useEffect(() => {
    if (status === "anonymous" && location.pathname !== "/auth") navigate("/auth", { replace: true });
  }, [status, navigate, location.pathname]);

  useEffect(() => {
    if (status !== "authenticated") {
      setRecentChats([]);
      return;
    }
    void api
      .listChats(role)
      .then((result) => setRecentChats((result.chats || []).slice(0, 6)))
      .catch(() => setRecentChats([]));
  }, [role, status]);

  if (status === "loading") {
    return (
      <div className="grid min-h-dvh place-items-center bg-background text-sm text-muted-foreground">
        <div className="flex items-center gap-3 rounded-[6px] border bg-card/80 px-4 py-3 shadow-none">
          <Sparkles className="size-4 animate-pulse text-primary" />
          正在恢复会话...
        </div>
      </div>
    );
  }

  const visibleSections = navSections.filter((section) => !section.role || section.role === role);

  return (
    <SidebarProvider>
      <a href="#main-content" className="skip-link">
        跳到主要内容
      </a>
      <Sidebar collapsible="icon" variant="inset" className="border-sidebar-border">
          <SidebarHeader className="gap-3">
            <Link
              to="/"
              className="group flex min-h-12 items-center gap-3 rounded-[6px] px-2 py-2 text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            >
              <div className="grid size-9 shrink-0 place-items-center rounded-[6px] border border-sidebar-border bg-sidebar-primary text-sidebar-primary-foreground shadow-none">
                <BrainCircuit className="size-4" aria-hidden="true" />
              </div>
              <div className="min-w-0 group-data-[collapsible=icon]:hidden">
                <p className="truncate text-sm font-semibold">EduMind</p>
                <p className="truncate text-xs text-sidebar-foreground/60">Agent workspace</p>
              </div>
            </Link>
            <div className="px-2 group-data-[collapsible=icon]:hidden">
              <SegmentedControl<Role>
                value={role}
                onChange={setRole}
                options={[
                  { value: "student", label: "学生" },
                  { value: "teacher", label: "教师" },
                ]}
              />
            </div>
          </SidebarHeader>

          <SidebarContent>
            {visibleSections.map((section) => (
              <SidebarGroup key={section.title}>
                <SidebarGroupLabel>{section.title}</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {section.items.map((item) => (
                      <SidebarMenuItem key={item.href}>
                        <SidebarMenuButton
                          asChild
                          isActive={isNavItemActive(item, location.pathname)}
                          className="min-h-9"
                        >
                          <NavLink to={item.href} end={item.href === "/"}>
                            <item.icon className="size-4" aria-hidden="true" />
                            <span>{item.label}</span>
                          </NavLink>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            ))}

            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupLabel>最近对话</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {recentChats.length ? (
                    recentChats.map((chat) => (
                      <SidebarMenuItem key={chat.id}>
                        <SidebarMenuButton asChild>
                          <Link to={`/workspace/chat?chatId=${encodeURIComponent(chat.id)}&role=${role}`}>
                            <BrainCircuit className="size-4" aria-hidden="true" />
                            <span>{chat.title || "未命名对话"}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))
                  ) : (
                    <SidebarMenuItem className="px-2 py-1 text-xs leading-5 text-sidebar-foreground/55 group-data-[collapsible=icon]:hidden">
                      暂无最近对话
                    </SidebarMenuItem>
                  )}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter>
            <div className="rounded-[6px] border border-sidebar-border bg-sidebar-accent/45 p-2 group-data-[collapsible=icon]:hidden">
              <div className="flex items-center gap-2">
                <Avatar className="size-8 rounded-md">
                  <AvatarFallback className="rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
                    {(user?.username || "U").slice(0, 1).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{user?.username || "未登录"}</p>
                  <p className="truncate text-xs text-sidebar-foreground/60">API Gateway</p>
                </div>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <Button variant="outline" size="sm" className="h-8 bg-sidebar" asChild>
                  <Link to="/files">文件 {files.length}</Link>
                </Button>
                <Button variant="ghost" size="sm" className="h-8" onClick={() => void logout()}>
                  退出
                </Button>
              </div>
            </div>
          </SidebarFooter>
          <SidebarRail />
      </Sidebar>

      <SidebarInset className="min-w-0">
          <header className="sticky top-0 z-30 flex min-h-14 shrink-0 items-center gap-2 border-b bg-background/92 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/75">
            <SidebarTrigger className="-ml-1" aria-label="切换侧栏">
              <PanelLeft className="size-4" />
            </SidebarTrigger>
            <Separator orientation="vertical" className="mx-1 h-4" />
            <div className="min-w-0 flex-1">
              <div className="flex min-w-0 items-center gap-2">
                <h1 className="truncate text-sm font-semibold">{pageTitleFor(location.pathname, role)}</h1>
                <Badge variant={role === "teacher" ? "info" : "secondary"}>
                  {role === "teacher" ? "教师端" : "学生端"}
                </Badge>
              </div>
              <p className="hidden truncate text-xs text-muted-foreground sm:block">
                多文件 RAG、Agent 对话、生成任务与学习记录统一工作区
              </p>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <AccountMenu userLabel={user?.username || "未登录"} onLogout={() => void logout()} />
            </div>
          </header>
          <main id="main-content" className="min-h-0 flex-1 p-3 sm:p-4 lg:p-6">
            <Outlet />
          </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

function AccountMenu({ userLabel, onLogout }: { userLabel: string; onLogout: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-9 gap-2 px-2">
          <Avatar className="size-7 rounded-md">
            <AvatarFallback className="rounded-md bg-primary text-primary-foreground">
              {userLabel.slice(0, 1).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span className="hidden max-w-28 truncate text-sm md:inline">{userLabel}</span>
          <ChevronDown className="size-3.5 text-muted-foreground" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex items-center gap-2">
            <UserRound className="size-4" />
            <span className="truncate">{userLabel}</span>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled>
          <Settings className="size-4" />
          账户设置
        </DropdownMenuItem>
        <DropdownMenuItem variant="destructive" onClick={onLogout}>
          <LogOut className="size-4" />
          退出登录
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(() => localStorage.getItem("edumind.react.theme") !== "light");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("edumind.react.theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon" onClick={() => setDark((next) => !next)} aria-label="切换主题">
          <Sun className={cn("size-4", dark && "hidden")} />
          <Moon className={cn("size-4", !dark && "hidden")} />
        </Button>
      </TooltipTrigger>
      <TooltipContent>切换主题</TooltipContent>
    </Tooltip>
  );
}

function isNavItemActive(item: NavItem, pathname: string) {
  const hrefPath = item.href.split("?")[0];
  return pathname === hrefPath || Boolean(item.activeHrefs?.includes(pathname));
}

function pageTitleFor(pathname: string, role: Role) {
  const allItems = navSections.flatMap((section) => section.items);
  const matched = allItems.find((item) => isNavItemActive(item, pathname));
  if (matched) return matched.label;
  if (pathname.startsWith("/workspace")) return role === "teacher" ? "教学 Agent" : "学习 Agent";
  if (pathname === "/files") return role === "teacher" ? "教师文件库" : "文件库";
  return "项目首页";
}
