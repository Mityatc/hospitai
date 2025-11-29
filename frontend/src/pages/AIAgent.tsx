import { useState } from "react";
import { Bot, Play, Zap, CheckCircle, XCircle, Info, Clock, Brain, Eye, ListChecks, Rocket, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useRunAgent, useApproveAction, useRejectAction, useAgentStatus } from "@/hooks/useApi";
import { getAIAnalysis, type AgentResponse, type AgentAction, type AgentIssue } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function AIAgent() {
  const [autonomousMode, setAutonomousMode] = useState(false);
  const [agentResults, setAgentResults] = useState<AgentResponse | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [reasoningOpen, setReasoningOpen] = useState(false);

  const { data: agentStatus } = useAgentStatus();
  const runAgentMutation = useRunAgent();
  const approveActionMutation = useApproveAction();
  const rejectActionMutation = useRejectAction();

  const handleRunAgent = async () => {
    try {
      const results = await runAgentMutation.mutateAsync({
        hospitalId: 'H001',
        autonomousMode
      });
      setAgentResults(results);
    } catch (error) {
      console.error('Failed to run agent:', error);
    }
  };

  const handleApprove = async (actionId: number) => {
    try {
      await approveActionMutation.mutateAsync(actionId);
      // Refresh agent results
      if (agentResults) {
        setAgentResults({
          ...agentResults,
          actions_pending: agentResults.actions_pending.filter(a => a.id !== actionId),
          actions_executed: [
            ...agentResults.actions_executed,
            { ...agentResults.actions_pending.find(a => a.id === actionId)!, status: 'executed' }
          ]
        });
      }
    } catch (error) {
      console.error('Failed to approve action:', error);
    }
  };

  const handleReject = async (actionId: number) => {
    try {
      await rejectActionMutation.mutateAsync(actionId);
      if (agentResults) {
        setAgentResults({
          ...agentResults,
          actions_pending: agentResults.actions_pending.filter(a => a.id !== actionId)
        });
      }
    } catch (error) {
      console.error('Failed to reject action:', error);
    }
  };

  const handleGetAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      const response = await getAIAnalysis('H001');
      setAiAnalysis(response.analysis);
    } catch (error) {
      console.error('Failed to get AI analysis:', error);
      setAiAnalysis('Failed to generate AI analysis. Please check if the backend is running and Gemini API is configured.');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'emergency': return 'border-emergency/30 bg-emergency/5';
      case 'critical': return 'border-critical/30 bg-critical/5';
      case 'warning': return 'border-warning/30 bg-warning/5';
      default: return 'border-primary/30 bg-primary/5';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'emergency':
      case 'critical':
        return <Zap className="h-4 w-4 text-critical" />;
      case 'warning':
        return <Info className="h-4 w-4 text-warning" />;
      default:
        return <Info className="h-4 w-4 text-primary" />;
    }
  };

  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      {/* Agent Status Header */}
      <Card className="border-primary/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary/10 relative">
                <Bot className="h-8 w-8 text-primary" />
                {agentStatus?.initialized && (
                  <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-success animate-pulse" />
                )}
              </div>
              <div>
                <CardTitle className="text-2xl">AI Agent</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {agentResults 
                    ? `Last analysis: ${new Date(agentResults.timestamp).toLocaleString()}`
                    : 'Ready to analyze'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  id="autonomous-mode"
                  checked={autonomousMode}
                  onCheckedChange={setAutonomousMode}
                />
                <Label htmlFor="autonomous-mode" className="text-sm">
                  Autonomous Mode
                </Label>
              </div>
              <Button
                onClick={handleRunAgent}
                disabled={runAgentMutation.isPending}
                className="gap-2"
              >
                {runAgentMutation.isPending ? (
                  <>
                    <Clock className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Run Analysis
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Agent Thinking Animation */}
      {runAgentMutation.isPending && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <div className="h-4 w-4 rounded-full bg-primary animate-pulse" />
                </div>
                <div>
                  <p className="font-medium">Agent Thinking</p>
                  <p className="text-sm text-muted-foreground">Processing hospital data...</p>
                </div>
              </div>
              
              {/* Step indicators */}
              <div className="flex items-center gap-2 mt-4">
                {[
                  { icon: Eye, label: 'PERCEIVE' },
                  { icon: Brain, label: 'REASON' },
                  { icon: ListChecks, label: 'PLAN' },
                  { icon: Rocket, label: 'EXECUTE' }
                ].map((step, i) => (
                  <div key={step.label} className="flex items-center">
                    <div className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                      "bg-primary/20 text-primary animate-pulse"
                    )}>
                      <step.icon className="h-3 w-3" />
                      {step.label}
                    </div>
                    {i < 3 && <div className="w-4 h-0.5 bg-primary/30 mx-1" />}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {agentResults && (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Situation Assessment */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-primary" />
                  Situation Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm text-muted-foreground mb-1">Bed Occupancy</p>
                    <p className="text-2xl font-bold font-mono">
                      {agentResults.situation.metrics?.bed_occupancy || 0}%
                    </p>
                    <p className={cn(
                      "text-xs mt-1",
                      agentResults.situation.trends?.direction === 'increasing' ? "text-critical" : "text-success"
                    )}>
                      {agentResults.situation.trends?.direction === 'increasing' ? '↑' : '↓'} {agentResults.situation.trends?.direction}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm text-muted-foreground mb-1">ICU Occupancy</p>
                    <p className="text-2xl font-bold font-mono">
                      {agentResults.situation.metrics?.icu_occupancy || 0}%
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {agentResults.situation.metrics?.available_icu || 0} beds available
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm text-muted-foreground mb-1">Staff Ratio</p>
                    <p className="text-2xl font-bold font-mono">
                      {agentResults.situation.metrics?.staff_ratio?.toFixed(2) || 0}
                    </p>
                    <p className={cn(
                      "text-xs mt-1",
                      (agentResults.situation.metrics?.staff_ratio || 0) < 0.15 ? "text-critical" : "text-success"
                    )}>
                      {(agentResults.situation.metrics?.staff_ratio || 0) < 0.15 ? '⚠ Below Target' : '✓ Normal'}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50">
                    <p className="text-sm text-muted-foreground mb-1">Ventilator Usage</p>
                    <p className="text-2xl font-bold font-mono">
                      {agentResults.situation.metrics?.ventilator_usage || 0}%
                    </p>
                    <p className="text-xs text-success mt-1">✓ Normal</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Issues Detected */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-warning" />
                  Issues Detected ({agentResults.issues.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[250px]">
                  <div className="space-y-3">
                    {agentResults.issues.length === 0 ? (
                      <div className="p-4 rounded-lg border border-success/30 bg-success/5 text-center">
                        <CheckCircle className="h-8 w-8 text-success mx-auto mb-2" />
                        <p className="font-medium text-success">No Critical Issues</p>
                        <p className="text-xs text-muted-foreground mt-1">All systems operating normally</p>
                      </div>
                    ) : (
                      agentResults.issues.map((issue, idx) => (
                        <div key={idx} className={cn("p-4 rounded-lg border", getSeverityColor(issue.severity))}>
                          <div className="flex items-start gap-3">
                            <div className="p-1 rounded bg-background/50">
                              {getSeverityIcon(issue.severity)}
                            </div>
                            <div className="flex-1">
                              <p className="font-semibold text-sm">{issue.message}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Type: {issue.type} • Resource: {issue.resource}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Recommended Actions */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <ListChecks className="h-5 w-5 text-primary" />
                  Actions ({agentResults.actions_pending.length} Pending, {agentResults.actions_executed.length} Executed)
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {agentResults.actions_pending.length === 0 && agentResults.actions_executed.length === 0 ? (
                <div className="p-6 text-center text-muted-foreground">
                  <p>No actions generated. The situation appears stable.</p>
                </div>
              ) : (
                <>
                  {/* Pending Actions */}
                  {agentResults.actions_pending.map((action) => (
                    <ActionCard
                      key={action.id}
                      action={action}
                      onApprove={() => handleApprove(action.id)}
                      onReject={() => handleReject(action.id)}
                      isApproving={approveActionMutation.isPending}
                      isRejecting={rejectActionMutation.isPending}
                    />
                  ))}
                  
                  {/* Executed Actions */}
                  {agentResults.actions_executed.map((action) => (
                    <ActionCard key={action.id} action={action} executed />
                  ))}
                </>
              )}
            </CardContent>
          </Card>

          {/* Reasoning Trace */}
          <Collapsible open={reasoningOpen} onOpenChange={setReasoningOpen}>
            <Card>
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Brain className="h-5 w-5 text-primary" />
                      Agent Reasoning Trace
                    </span>
                    <Badge variant="outline">{reasoningOpen ? 'Click to collapse' : 'Click to expand'}</Badge>
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <pre className="whitespace-pre-wrap text-xs bg-muted/50 p-4 rounded-lg">
                        {agentResults.reasoning_trace}
                      </pre>
                    </div>
                  </ScrollArea>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>

          {/* AI Analysis */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary" />
                  AI Analysis & Recommendations
                </CardTitle>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleGetAnalysis}
                  disabled={analysisLoading}
                  className="gap-2"
                >
                  {analysisLoading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4" />
                      Generate Analysis
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {aiAnalysis ? (
                <ScrollArea className="h-[300px]">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap">{aiAnalysis}</div>
                  </div>
                </ScrollArea>
              ) : (
                <div className="p-6 text-center text-muted-foreground">
                  <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Click "Generate Analysis" to get AI-powered insights and recommendations.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Initial State - No Results Yet */}
      {!agentResults && !runAgentMutation.isPending && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Bot className="h-16 w-16 mx-auto mb-4 text-primary/50" />
              <h3 className="text-xl font-semibold mb-2">Ready to Analyze</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                The AI Agent uses a ReAct architecture to perceive hospital data, reason about issues, 
                plan actions, and execute responses.
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-6">
                {[
                  { icon: Eye, label: 'PERCEIVE', desc: 'Gather metrics' },
                  { icon: Brain, label: 'REASON', desc: 'Analyze patterns' },
                  { icon: ListChecks, label: 'PLAN', desc: 'Generate actions' },
                  { icon: Rocket, label: 'EXECUTE', desc: 'Take action' }
                ].map((step) => (
                  <div key={step.label} className="p-4 rounded-lg bg-muted/50 text-center">
                    <step.icon className="h-6 w-6 mx-auto mb-2 text-primary" />
                    <p className="font-medium text-sm">{step.label}</p>
                    <p className="text-xs text-muted-foreground">{step.desc}</p>
                  </div>
                ))}
              </div>
              
              <Button onClick={handleRunAgent} size="lg" className="gap-2">
                <Play className="h-5 w-5" />
                Start Analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Action Card Component
function ActionCard({ 
  action, 
  executed = false,
  onApprove,
  onReject,
  isApproving = false,
  isRejecting = false
}: { 
  action: AgentAction;
  executed?: boolean;
  onApprove?: () => void;
  onReject?: () => void;
  isApproving?: boolean;
  isRejecting?: boolean;
}) {
  return (
    <div className={cn(
      "p-4 rounded-lg border transition-all",
      executed ? "border-success/30 bg-success/5" : "border-primary/30 bg-primary/5"
    )}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex">
              {Array.from({ length: 5 }).map((_, i) => (
                <span
                  key={i}
                  className={cn(
                    "text-lg",
                    i < action.priority ? "text-warning" : "text-muted/30"
                  )}
                >
                  ★
                </span>
              ))}
            </div>
            <Badge variant="outline" className="text-xs">
              {action.action_type}
            </Badge>
            {action.auto_executed && (
              <Badge className="bg-primary/20 text-primary text-xs">
                Auto-execute
              </Badge>
            )}
          </div>
          <h4 className="font-semibold mb-1">{action.description}</h4>
          {action.details && Object.keys(action.details).length > 0 && (
            <p className="text-sm text-muted-foreground mb-2">
              {JSON.stringify(action.details)}
            </p>
          )}
        </div>

        <div className="flex gap-2">
          {executed ? (
            <Badge className="bg-success text-success-foreground">
              <CheckCircle className="h-3 w-3 mr-1" />
              Executed
            </Badge>
          ) : (
            <>
              <Button
                size="sm"
                onClick={onApprove}
                disabled={isApproving}
                className="gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onReject}
                disabled={isRejecting}
                className="gap-2"
              >
                <XCircle className="h-4 w-4" />
                Reject
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
