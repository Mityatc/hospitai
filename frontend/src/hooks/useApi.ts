/**
 * React Query hooks for HospitAI API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDashboardSummary,
  getTrends,
  getPredictions,
  getAgentStatus,
  runAgent,
  approveAction,
  rejectAction,
  getAIAnalysis,
  getAgentLog,
  getLiveData,
  getApiStatus,
  getHospitals,
  getAlerts,
  healthCheck,
  type DashboardData,
  type AgentResponse,
} from '@/lib/api';

// Query keys
export const queryKeys = {
  dashboard: (hospitalId: string) => ['dashboard', hospitalId] as const,
  trends: (hospitalId: string, days: number) => ['trends', hospitalId, days] as const,
  predictions: (hospitalId: string, days: number) => ['predictions', hospitalId, days] as const,
  agentStatus: ['agent', 'status'] as const,
  agentLog: ['agent', 'log'] as const,
  liveData: (city: string) => ['liveData', city] as const,
  apiStatus: ['apiStatus'] as const,
  hospitals: ['hospitals'] as const,
  alerts: (hospitalId: string) => ['alerts', hospitalId] as const,
  health: ['health'] as const,
};

/**
 * Hook for dashboard summary data
 */
export function useDashboard(hospitalId: string = 'H001', days: number = 30) {
  return useQuery({
    queryKey: queryKeys.dashboard(hospitalId),
    queryFn: () => getDashboardSummary(hospitalId, days),
    refetchInterval: false, // Disabled - only refresh on manual click
    staleTime: 60000, // Data considered fresh for 1 minute
  });
}

/**
 * Hook for trend data
 */
export function useTrends(hospitalId: string = 'H001', days: number = 30) {
  return useQuery({
    queryKey: queryKeys.trends(hospitalId, days),
    queryFn: () => getTrends(hospitalId, days),
    staleTime: 60000,
  });
}

/**
 * Hook for predictions
 */
export function usePredictions(hospitalId: string = 'H001', days: number = 7) {
  return useQuery({
    queryKey: queryKeys.predictions(hospitalId, days),
    queryFn: () => getPredictions(hospitalId, days),
    staleTime: 60000,
  });
}

/**
 * Hook for agent status
 */
export function useAgentStatus() {
  return useQuery({
    queryKey: queryKeys.agentStatus,
    queryFn: getAgentStatus,
    staleTime: 5000,
  });
}

/**
 * Hook for running agent analysis
 */
export function useRunAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ hospitalId, autonomousMode }: { hospitalId: string; autonomousMode: boolean }) =>
      runAgent(hospitalId, autonomousMode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agentStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentLog });
    },
  });
}

/**
 * Hook for approving agent action
 */
export function useApproveAction() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (actionId: number) => approveAction(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agentStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentLog });
    },
  });
}

/**
 * Hook for rejecting agent action
 */
export function useRejectAction() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (actionId: number) => rejectAction(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agentStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentLog });
    },
  });
}

/**
 * Hook for AI analysis
 */
export function useAIAnalysis(hospitalId: string = 'H001', enabled: boolean = false) {
  return useQuery({
    queryKey: ['aiAnalysis', hospitalId],
    queryFn: () => getAIAnalysis(hospitalId),
    enabled,
    staleTime: 300000, // 5 minutes
  });
}

/**
 * Hook for agent log
 */
export function useAgentLog() {
  return useQuery({
    queryKey: queryKeys.agentLog,
    queryFn: getAgentLog,
    staleTime: 10000,
  });
}

/**
 * Hook for live environmental data
 */
export function useLiveData(city: string = 'Delhi', enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.liveData(city),
    queryFn: () => getLiveData(city),
    enabled,
    staleTime: 60000,
    refetchInterval: 300000, // Refresh every 5 minutes
  });
}

/**
 * Hook for API status
 */
export function useApiStatus() {
  return useQuery({
    queryKey: queryKeys.apiStatus,
    queryFn: getApiStatus,
    staleTime: 60000,
  });
}

/**
 * Hook for hospitals list
 */
export function useHospitals() {
  return useQuery({
    queryKey: queryKeys.hospitals,
    queryFn: getHospitals,
    staleTime: 300000,
  });
}

/**
 * Hook for alerts
 */
export function useAlerts(hospitalId: string = 'H001') {
  return useQuery({
    queryKey: queryKeys.alerts(hospitalId),
    queryFn: () => getAlerts(hospitalId),
    refetchInterval: false, // Disabled auto-refresh
    staleTime: 60000,
  });
}

/**
 * Hook for health check
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: healthCheck,
    retry: 3,
    retryDelay: 1000,
  });
}
