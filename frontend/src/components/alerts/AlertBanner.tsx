import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AlertBannerProps {
  severity: "warning" | "critical" | "emergency";
  message: string;
  onDismiss?: () => void;
}

export const AlertBanner = ({ severity, message, onDismiss }: AlertBannerProps) => {
  const severityStyles = {
    warning: "bg-warning/20 text-warning border-warning/30",
    critical: "bg-critical/20 text-critical border-critical/30",
    emergency: "bg-emergency/20 text-emergency border-emergency/30 animate-pulse"
  };

  return (
    <div className={cn(
      "flex items-center justify-between gap-4 px-6 py-3 border-b animate-in slide-in-from-top-2 duration-300",
      severityStyles[severity]
    )}>
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-5 w-5" />
        <span className="font-medium">{message}</span>
      </div>
      {onDismiss && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};
