import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function MetricGrid({
  metrics,
}: {
  metrics: Array<{ label: string; value: string | number; detail: string; icon: LucideIcon; tone?: "success" | "warning" | "info" }>;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.label}>
          <CardContent className="flex items-start justify-between gap-4 p-4">
            <div>
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{metric.value}</p>
              <p className="mt-1 text-xs text-muted-foreground">{metric.detail}</p>
            </div>
            <Badge variant={metric.tone ?? "secondary"} className="p-2">
              <metric.icon className="h-4 w-4" aria-hidden="true" />
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
