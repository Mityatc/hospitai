import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LayoutDashboard, Bot, TrendingUp, Database, Cloud, LogOut } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { AlertBanner } from "@/components/alerts/AlertBanner";
import { NavLink } from "@/components/NavLink";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Button } from "@/components/ui/button";
import Dashboard from "./pages/Dashboard";
import AIAgent from "./pages/AIAgent";
import Predictions from "./pages/Predictions";
import LiveData from "./pages/LiveData";
import DataUpload from "./pages/DataUpload";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
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

// Main app layout with sidebar (for authenticated users)
const MainLayout = () => {
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [dismissedAlerts, setDismissedAlerts] = useState<number[]>([]);
  const { user, signOut } = useAuth();

  const { data: alertsData } = useAlerts('H001');
  const { isError: backendOffline } = useHealthCheck();

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  const activeAlerts = alertsData?.alerts.filter(a => !dismissedAlerts.includes(a.id)) || [];
  const topAlert = activeAlerts[0];

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <div className="min-h-screen bg-background">
      <Header theme={theme} onThemeToggle={toggleTheme} />
      
      {backendOffline && (
        <AlertBanner
          severity="warning"
          message="⚠️ Backend API offline - showing sample data. Start the API with: uvicorn api:app --reload"
          onDismiss={() => {}}
        />
      )}
      
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
                Data Sources
              </p>
              <NavLink
                to="/data-upload"
                className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-muted/50"
                activeClassName="bg-primary/10 text-primary font-medium"
              >
                <Database className="h-5 w-5" />
                <span>Data Upload</span>
              </NavLink>
              <NavLink
                to="/live-data"
                className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors hover:bg-muted/50"
                activeClassName="bg-primary/10 text-primary font-medium"
              >
                <Cloud className="h-5 w-5" />
                <span>Live Data</span>
              </NavLink>
            </div>

            {/* User Info & Logout */}
            <div className="pt-4 mt-4 border-t border-border">
              <div className="px-4 py-2">
                <div className="flex items-center gap-2 mb-2">
                  <div className={cn(
                    "h-2 w-2 rounded-full",
                    backendOffline ? "bg-critical" : "bg-success animate-pulse"
                  )} />
                  <span className="text-xs text-muted-foreground">
                    {backendOffline ? 'API Offline' : 'API Connected'}
                  </span>
                </div>
                {user && (
                  <div className="mt-3 p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground">Signed in as</p>
                    <p className="text-sm font-medium truncate">{user.email}</p>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleSignOut}
                      className="w-full mt-2 gap-2"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </Button>
                  </div>
                )}
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
            <Route path="/live-data" element={<LiveData />} />
            <Route path="/data-upload" element={<DataUpload />} />
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
        <AuthProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              
              {/* Protected routes */}
              <Route path="/*" element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              } />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
