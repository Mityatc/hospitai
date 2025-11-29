import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  icon: LucideIcon;
  title: string;
  value: string;
  subtitle: string;
  trend: {
    direction: "up" | "down" | "stable";
    value: string;
  };
  percentage?: number;
  threshold?: { yellow: number; red: number };
}

export const MetricCard = ({
  icon: Icon,
  title,
  value,
  subtitle,
  trend,
  percentage,
  threshold = { yellow: 70, red: 85 }
}: MetricCardProps) => {
  const getColorByPercentage = (pct: number) => {
    if (pct >= threshold.red) return "critical";
    if (pct >= threshold.yellow) return "warning";
    return "success";
  };

  const color = percentage ? getColorByPercentage(percentage) : "primary";

  const TrendIcon = trend.direction === "up" ? TrendingUp : trend.direction === "down" ? TrendingDown : Minus;

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className={cn(
            "p-2 rounded-lg",
            color === "success" && "bg-success/10 text-success",
            color === "warning" && "bg-warning/10 text-warning",
            color === "critical" && "bg-critical/10 text-critical",
            color === "primary" && "bg-primary/10 text-primary"
          )}>
            <Icon className="h-5 w-5" />
          </div>
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono">{value}</span>
          </div>
          <p className="text-sm text-muted-foreground">{subtitle}</p>

          {percentage !== undefined && (
            <Progress 
              value={percentage} 
              className={cn(
                "h-2 mt-3",
                color === "success" && "[&>div]:bg-success",
                color === "warning" && "[&>div]:bg-warning",
                color === "critical" && "[&>div]:bg-critical"
              )}
            />
          )}

          <div className="flex items-center gap-1 text-xs">
            <TrendIcon className={cn(
              "h-3 w-3",
              trend.direction === "up" && "text-critical",
              trend.direction === "down" && "text-success",
              trend.direction === "stable" && "text-muted-foreground"
            )} />
            <span className="text-muted-foreground">{trend.value}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
