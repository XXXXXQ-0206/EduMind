import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { BrainCircuit } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SegmentedControl } from "@/components/ui/tabs";
import { useAuthStore } from "@/stores/auth-store";

export function AuthPage() {
  const { status, login, register, error } = useAuthStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (status === "authenticated") return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      if (mode === "login") await login(username, password);
      else await register(username, password);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-dvh place-items-center bg-background px-4 py-8">
      <Card className="w-full max-w-md bg-card/72 shadow-none">
        <CardHeader>
          <div className="mb-3 grid size-12 place-items-center rounded-[6px] border border-primary/35 bg-primary/14 text-primary">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <CardTitle className="text-xl">进入 EduMind</CardTitle>
          <CardDescription>使用同一账号访问文件库、RAG 检索和生成任务。</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <SegmentedControl value={mode} onChange={setMode} options={[{ value: "login", label: "登录" }, { value: "register", label: "注册" }]} />
            <div className="grid gap-2">
              <Label htmlFor="username">用户名</Label>
              <Input id="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            {error ? (
              <Alert variant="destructive">
                <AlertTitle>认证失败</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
            <Button className="w-full" loading={busy}>{mode === "login" ? "登录" : "创建账号"}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
