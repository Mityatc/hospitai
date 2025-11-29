import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface CapacityGaugeProps {
  title: string;
  value: number;
  total: number;
  percentage: number;
  threshold?: { yellow: number; red: number };
}

export const CapacityGauge = ({
  title,
  value,
  total,
  percentage,
  threshold = { yellow: 70, red: 85 }
}: CapacityGaugeProps) => {
  const getColor = (pct: number) => {
    if (pct >= threshold.red) return "critical";
    if (pct >= threshold.yellow) return "warning";
    return "success";
  };

  const color = getColor(percentage);
  const rotation = (percentage / 100) * 180;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center pb-6">
        <div className="relative w-40 h-20 mb-4">
          {/* Background arc */}
          <svg className="w-full h-full" viewBox="0 0 160 80">
            <path
              d="M 10 70 A 60 60 0 0 1 150 70"
              fill="none"
              stroke="currentColor"
              strokeWidth="12"
              className="text-muted/20"
            />
            {/* Colored arc */}
            <path
              d="M 10 70 A 60 60 0 0 1 150 70"
              fill="none"
              stroke="currentColor"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(percentage / 100) * 220} 220`}
              className={cn(
                color === "success" && "text-success",
                color === "warning" && "text-warning",
                color === "critical" && "text-critical"
              )}
              style={{
                transition: "stroke-dasharray 1s ease-in-out"
              }}
            />
            {/* Threshold markers */}
            <line
              x1="80"
              y1="70"
              x2="80"
              y2="15"
              stroke="currentColor"
              strokeWidth="2"
              className="text-muted/30"
              transform={`rotate(${(threshold.yellow / 100) * 180 - 90} 80 70)`}
            />
            <line
              x1="80"
              y1="70"
              x2="80"
              y2="15"
              stroke="currentColor"
              strokeWidth="2"
              className="text-muted/30"
              transform={`rotate(${(threshold.red / 100) * 180 - 90} 80 70)`}
            />
          </svg>
          
          {/* Center value */}
          <div className="absolute inset-0 flex items-end justify-center pb-2">
            <div className="text-center">
              <div className="text-2xl font-bold font-mono">{percentage}%</div>
              <div className="text-xs text-muted-foreground">{value}/{total}</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
