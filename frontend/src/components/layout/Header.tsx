import { Activity, Bell, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  theme: "light" | "dark";
  onThemeToggle: () => void;
}

export const Header = ({ theme, onThemeToggle }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="h-8 w-8 text-primary animate-pulse" />
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="text-primary">Hospit</span>
              <span className="text-foreground">AI</span>
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs font-medium text-success uppercase tracking-wider">LIVE</span>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                City General Hospital
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem>City General Hospital</DropdownMenuItem>
              <DropdownMenuItem>Regional Medical Center</DropdownMenuItem>
              <DropdownMenuItem>Metropolitan Health</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            {new Date().toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={onThemeToggle}
            className="relative"
          >
            {theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center bg-critical text-[10px]">
              3
            </Badge>
          </Button>

          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-medium text-primary">
            AD
          </div>
        </div>
      </div>
    </header>
  );
};
