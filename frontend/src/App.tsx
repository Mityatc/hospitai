import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { LayoutDashboard, Bot, TrendingUp, Database, Cloud } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { AlertBanner } from "@/components/alerts/AlertBanner";
import { NavLink } from "@/components/NavLink";
import Dashboard from "./pages/Dashboard";
import AIAgent from "./pages/AIAgent";
import Predictions from "./pages/Predictions";
import NotFound from "./pages/NotFound";
import { cn } from "@/lib/utils";
import { useAlerts, useHealthCheck } from "@/hooks/useApi";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 10000,
    },
  },
});

// Inner app component that uses hooks
const AppContent = () => {
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [dismissedAlerts, setDismissedAlerts] = useState<number[]>([]);

  const { data: alertsData } = useAlerts('H001');
  const { data: healthData, isError: backendOffline } = useHealthCheck();

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  // Get active alerts (not dismissed)
  const activeAlerts = alertsData?.alerts.filter(a => !dismissedAlerts.includes(a.id)) || [];
  const topAlert = activeAlerts[0];

  return (
    <div className="min-h-screen bg-background">
      <Header theme={theme} onThemeToggle={toggleTheme} />
      
      {/* Backend offline warning */}
      {backendOffline && (
        <AlertBanner
          severity="warning"
          message="⚠️ Backend API offline - showing sample data. Start the API with: uvicorn api:app --reload"
          onDismiss={() => {}}
        />
      )}
      
      {/* Dynamic alerts from API */}
      {topAlert && !backendOffline && (
        <AlertBanner
          severity={topAlert.severity as any}
          message={topAlert.message}
          onDismiss={() => setDismissedAlerts(prev => [...prev, topAlert.id])}
        />
      )}

            <div className="flex w-full">
              {/* Sidebar Navigation */}
              <aside className="w-64 border-r border-border min-h-[calc(100vh-4rem)] bg-card/50">
                <nav className="p-4 space-y-2">
                  <NavLink
                    to="/"
                    end
                    className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-muted/50"
                    activeClassName="bg-primary/10 text-primary font-medium"
                  >
                    <LayoutDashboard className="h-5 w-5" />
                    <span>Dashboard</span>
                  </NavLink>
                  
                  <NavLink
                    to="/ai-agent"
                    className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-muted/50"
                    activeClassName="bg-primary/10 text-primary font-medium"
                  >
                    <Bot className="h-5 w-5" />
                    <span>AI Agent</span>
                  </NavLink>
                  
                  <NavLink
                    to="/predictions"
                    className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-muted/50"
                    activeClassName="bg-primary/10 text-primary font-medium"
                  >
                    <TrendingUp className="h-5 w-5" />
                    <span>Predictions</span>
                  </NavLink>

                  <div className="pt-4 mt-4 border-t border-border">
                    <p className="px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      Coming Soon
                    </p>
                    <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-muted-foreground/50 cursor-not-allowed">
                      <Database className="h-5 w-5" />
                      <span>Data Upload</span>
                    </div>
                    <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-muted-foreground/50 cursor-not-allowed">
                      <Cloud className="h-5 w-5" />
                      <span>Live Data</span>
                    </div>
                  </div>

                  {/* API Status */}
                  <div className="pt-4 mt-4 border-t border-border">
                    <div className="px-4 py-2">
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "h-2 w-2 rounded-full",
                          backendOffline ? "bg-critical" : "bg-success animate-pulse"
                        )} />
                        <span className="text-xs text-muted-foreground">
                          {backendOffline ? 'API Offline' : 'API Connected'}
                        </span>
                      </div>
                    </div>
                  </div>
                </nav>
              </aside>

              {/* Main Content */}
              <main className="flex-1">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/ai-agent" element={<AIAgent />} />
                  <Route path="/predictions" element={<Predictions />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </main>
            </div>
          </div>
      );
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
