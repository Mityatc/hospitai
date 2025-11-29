import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskFactor {
  name: string;
  value: number;
  threshold: number;
  triggered: boolean;
}

interface RiskPanelProps {
  score: number;
  maxScore: number;
  level: string;
  factors: RiskFactor[];
}

export const RiskPanel = ({ score, maxScore, level, factors }: RiskPanelProps) => {
  const levelColors = {
    LOW: "success",
    MEDIUM: "warning",
    HIGH: "critical",
    CRITICAL: "emergency"
  };

  const color = levelColors[level as keyof typeof levelColors] || "warning";
  const percentage = (score / maxScore) * 100;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Risk Assessment</CardTitle>
          <Badge 
            className={cn(
              "text-xs font-semibold",
              color === "success" && "bg-success text-success-foreground",
              color === "warning" && "bg-warning text-warning-foreground",
              color === "critical" && "bg-critical text-critical-foreground",
              color === "emergency" && "bg-emergency text-emergency-foreground"
            )}
          >
            {level}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Risk Score</span>
            <span className="text-sm font-mono">{score}/{maxScore}</span>
          </div>
          <Progress 
            value={percentage}
            className={cn(
              "h-2",
              color === "success" && "[&>div]:bg-success",
              color === "warning" && "[&>div]:bg-warning",
              color === "critical" && "[&>div]:bg-critical",
              color === "emergency" && "[&>div]:bg-emergency"
            )}
          />
        </div>

        <div className="space-y-2">
          {factors.map((factor) => (
            <div
              key={factor.name}
              className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
            >
              <div className="flex items-center gap-2">
                {factor.triggered ? (
                  <AlertCircle className="h-4 w-4 text-critical" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-success" />
                )}
                <span className="text-sm font-medium">{factor.name}</span>
              </div>
              <div className="text-sm font-mono">
                <span className={cn(
                  factor.triggered ? "text-critical font-semibold" : "text-muted-foreground"
                )}>
                  {factor.value.toFixed(1)}
                </span>
                <span className="text-muted-foreground text-xs ml-1">
                  (&gt;{factor.threshold})
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
