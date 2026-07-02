import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export function Alert({
  title,
  children,
  variant = "info",
}: {
  title: string;
  children?: ReactNode;
  variant?: "info" | "success" | "destructive";
}) {
  const Icon = variant === "success" ? CheckCircle2 : variant === "destructive" ? AlertCircle : Info;
  return (
    <div
      role={variant === "destructive" ? "alert" : "status"}
      className={cn(
        "flex gap-3 rounded-lg border p-4 text-sm",
        variant === "destructive" && "border-destructive/30 bg-destructive/10 text-destructive",
        variant === "success" && "border-orange-500/25 bg-orange-500/10 text-orange-700 dark:text-orange-300",
        variant === "info" && "border-stone-500/25 bg-stone-500/10 text-stone-700 dark:text-stone-300",
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div className="space-y-1">
        <p className="font-medium">{title}</p>
        {children ? <div className="leading-6 text-foreground/80">{children}</div> : null}
      </div>
    </div>
  );
}

export function Progress({ value, label }: { value: number; label?: string }) {
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1">
      {label ? <div className="text-xs text-muted-foreground">{label}</div> : null}
      <div className="h-2 overflow-hidden rounded-full bg-muted" role="progressbar" aria-valuenow={bounded}>
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${bounded}%` }} />
      </div>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} />;
}
