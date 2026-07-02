import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function ScrollAreaShim({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("overflow-y-auto", className)}>{children}</div>;
}
