/**
 * HospitAI API Service
 * Connects React frontend to FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types
export interface Hospital {
  id: string;
  name: string;
  location: string;
}

export interface HospitalMetrics {
  total_beds: number;
  occupied_beds: number;
  bed_occupancy: number;
  total_icu: number;
  occupied_icu: number;
  icu_occupancy: number;
  total_ventilators: number;
  ventilators_used: number;
  ventilator_usage: number;
  staff_on_duty: number;
  staff_ratio: number;
}

export interface RiskFactor {
  name: string;
  value: number;
  threshold: number;
  triggered: boolean;
}

export interface RiskAssessment {
  score: number;
  max_score: number;
  level: string;
  factors: RiskFactor[];
}

export interface EnvironmentData {
  temperature: number;
  humidity: number;
  aqi: number;
  flu_cases: number;
}

export interface TrendData {
  bed_change_1d: number;
  bed_change_3d: number;
  bed_change_7d: number;
  icu_change_1d: number;
  direction: string;
  velocity: string;
}

export interface DashboardData {
  hospital: Hospital;
  metrics: HospitalMetrics;
  risk: RiskAssessment;
  environment: EnvironmentData;
  trends: TrendData;
  timestamp: string;
}

export interface TrendPoint {
  date: string;
  beds: number;
  icu: number;
  admissions: number;
  discharges: number;
}

export interface PredictionPoint {
  date: string;
  actual: number | null;
  predicted: number | null;
  upper_bound: number | null;
  lower_bound: number | null;
  risk_level: string | null;
}

export interface PredictionInsights {
  peak_occupancy: number;
  peak_date: string;
  days_until_threshold: number | null;
  threshold: number;
  recommendation: string;
}

export interface AgentIssue {
  type: string;
  resource: string;
  severity: string;
  value: number;
  message: string;
}

export interface AgentAction {
  id: number;
  action_type: string;
  description: string;
  priority: number;
  auto_executed: boolean;
  requires_approval: boolean;
  details: Record<string, any>;
  status: string;
}

export interface AgentResponse {
  situation: Record<string, any>;
  issues: AgentIssue[];
  actions_executed: AgentAction[];
  actions_pending: AgentAction[];
  reasoning_trace: string;
  timestamp: string;
}

export interface Alert {
  id: number;
  severity: 'info' | 'warning' | 'critical' | 'emergency';
  message: string;
  timestamp: string;
}

export interface LiveData {
  city: string;
  weather: {
    temperature: number;
    humidity: number;
    pressure: number;
    source: string;
  };
  air_quality: {
    aqi: number;
    pm25: number;
    pm10: number;
    source: string;
  };
  combined: Record<string, any>;
  timestamp: string;
}

// API Error class
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error - is the backend running?');
  }
}

// API Functions

/**
 * Get complete dashboard summary
 */
export async function getDashboardSummary(hospitalId: string = 'H001', days: number = 30): Promise<DashboardData> {
  return fetchApi<DashboardData>(`/api/dashboard/summary?hospital_id=${hospitalId}&days=${days}`);
}

/**
 * Get current hospital metrics
 */
export async function getMetrics(hospitalId: string = 'H001'): Promise<HospitalMetrics> {
  return fetchApi<HospitalMetrics>(`/api/dashboard/metrics?hospital_id=${hospitalId}`);
}

/**
 * Get historical trend data
 */
export async function getTrends(hospitalId: string = 'H001', days: number = 30): Promise<{ data: TrendPoint[]; days: number }> {
  return fetchApi(`/api/dashboard/trends?hospital_id=${hospitalId}&days=${days}`);
}

/**
 * Get ML predictions
 */
export async function getPredictions(hospitalId: string = 'H001', days: number = 7): Promise<{
  data: PredictionPoint[];
  insights: PredictionInsights | null;
  forecast_days: number;
}> {
  return fetchApi(`/api/predictions?hospital_id=${hospitalId}&days=${days}`);
}

/**
 * Get AI agent status
 */
export async function getAgentStatus(): Promise<{
  initialized: boolean;
  autonomous_mode: boolean;
  pending_actions: number;
  actions_taken: number;
}> {
  return fetchApi('/api/agent/status');
}

/**
 * Run AI agent analysis
 */
export async function runAgent(hospitalId: string = 'H001', autonomousMode: boolean = false): Promise<AgentResponse> {
  return fetchApi<AgentResponse>(`/api/agent/run?hospital_id=${hospitalId}&autonomous_mode=${autonomousMode}`, {
    method: 'POST',
  });
}

/**
 * Approve a pending agent action
 */
export async function approveAction(actionId: number): Promise<{ status: string; action_id: number }> {
  return fetchApi(`/api/agent/approve/${actionId}`, { method: 'POST' });
}

/**
 * Reject a pending agent action
 */
export async function rejectAction(actionId: number): Promise<{ status: string; action_id: number }> {
  return fetchApi(`/api/agent/reject/${actionId}`, { method: 'POST' });
}

/**
 * Get detailed AI analysis
 */
export async function getAIAnalysis(hospitalId: string = 'H001'): Promise<{ analysis: string; timestamp: string }> {
  return fetchApi(`/api/agent/analysis?hospital_id=${hospitalId}`);
}

/**
 * Get agent action log
 */
export async function getAgentLog(): Promise<{ log: any[] }> {
  return fetchApi('/api/agent/log');
}

/**
 * Get live environmental data
 */
export async function getLiveData(city: string = 'Delhi'): Promise<LiveData> {
  return fetchApi<LiveData>(`/api/live-data?city=${city}`);
}

/**
 * Get API status
 */
export async function getApiStatus(): Promise<{
  openweather_configured: boolean;
  api_key_preview: string;
}> {
  return fetchApi('/api/live-data/status');
}

/**
 * Get list of hospitals
 */
export async function getHospitals(): Promise<{ hospitals: Hospital[] }> {
  return fetchApi('/api/hospitals');
}

/**
 * Get current alerts
 */
export async function getAlerts(hospitalId: string = 'H001'): Promise<{ alerts: Alert[]; count: number }> {
  return fetchApi(`/api/alerts?hospital_id=${hospitalId}`);
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  return fetchApi('/');
}

// Export API base URL for debugging
export { API_BASE_URL };
