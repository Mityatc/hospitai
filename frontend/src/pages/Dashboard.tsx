import { Bed, Activity, Wind, Users, AlertTriangle, ThermometerSun, Droplets, Waves, RefreshCw } from "lucide-react";
import { MetricCard } from "@/components/metrics/MetricCard";
import { CapacityGauge } from "@/components/metrics/CapacityGauge";
import { TrendChart } from "@/components/charts/TrendChart";
import { RiskPanel } from "@/components/risk/RiskPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard, useTrends } from "@/hooks/useApi";
import { sampleDashboardData, trendData as sampleTrendData } from "@/lib/sampleData";

export default function Dashboard() {
  // Fetch real data from API
  const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError, refetch } = useDashboard('H001', 30);
  const { data: trendsResponse, isLoading: trendsLoading } = useTrends('H001', 30);

  // Use API data or fallback to sample data
  const data = dashboardData || sampleDashboardData;
  const trendData = trendsResponse?.data || sampleTrendData;
  
  const { metrics, risk, environment, trends } = data;

  const getAQILevel = (aqi: number) => {
    if (aqi <= 50) return { label: "Good", color: "bg-success text-success-foreground" };
    if (aqi <= 100) return { label: "Moderate", color: "bg-warning text-warning-foreground" };
    if (aqi <= 150) return { label: "Unhealthy", color: "bg-critical text-critical-foreground" };
    return { label: "Very Unhealthy", color: "bg-emergency text-emergency-foreground" };
  };

  const aqiLevel = getAQILevel(environment.aqi);

  // Loading skeleton
  if (dashboardLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {[...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-20 mb-4" />
                <Skeleton className="h-8 w-24 mb-2" />
                <Skeleton className="h-3 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-[200px] w-full rounded-lg" />
            <Skeleton className="h-[300px] w-full rounded-lg" />
          </div>
          <Skeleton className="h-[400px] w-full rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard Overview</h1>
          <p className="text-sm text-muted-foreground">
            {dashboardData ? `Last updated: ${new Date(dashboardData.timestamp).toLocaleTimeString()}` : 'Using sample data'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Error banner */}
      {dashboardError && (
        <div className="p-4 rounded-lg bg-warning/10 border border-warning/30 text-warning">
          <p className="text-sm">⚠️ Could not connect to backend API. Showing sample data.</p>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          icon={Bed}
          title="Total Beds"
          value={`${metrics.occupied_beds}/${metrics.total_beds}`}
          subtitle={`${metrics.bed_occupancy}% Occupancy`}
          percentage={metrics.bed_occupancy}
          trend={{
            direction: trends.bed_change_1d > 0 ? "up" : trends.bed_change_1d < 0 ? "down" : "stable",
            value: `${trends.bed_change_1d > 0 ? '+' : ''}${trends.bed_change_1d} today`
          }}
        />
        <MetricCard
          icon={Activity}
          title="ICU Beds"
          value={`${metrics.occupied_icu}/${metrics.total_icu}`}
          subtitle={`${metrics.icu_occupancy}% Occupancy`}
          percentage={metrics.icu_occupancy}
          trend={{
            direction: trends.icu_change_1d > 0 ? "up" : trends.icu_change_1d < 0 ? "down" : "stable",
            value: `${trends.icu_change_1d > 0 ? '+' : ''}${trends.icu_change_1d} today`
          }}
        />
        <MetricCard
          icon={Wind}
          title="Ventilators"
          value={`${metrics.ventilators_used}/${metrics.total_ventilators}`}
          subtitle={`${metrics.ventilator_usage}% Usage`}
          percentage={metrics.ventilator_usage}
          trend={{
            direction: "stable",
            value: "Stable"
          }}
        />
        <MetricCard
          icon={Users}
          title="Staff On Duty"
          value={metrics.staff_on_duty.toString()}
          subtitle={`Ratio: ${metrics.staff_ratio.toFixed(2)}`}
          trend={{
            direction: metrics.staff_ratio < 1 ? "down" : "stable",
            value: metrics.staff_ratio < 1 ? "Below target" : "On target"
          }}
        />
        <MetricCard
          icon={AlertTriangle}
          title="Risk Level"
          value={risk.level}
          subtitle={`Score: ${risk.score}/${risk.max_score}`}
          trend={{
            direction: risk.score >= 3 ? "up" : "stable",
            value: risk.score >= 3 ? "Elevated" : "Normal"
          }}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Capacity Gauges */}
          <div className="grid gap-4 sm:grid-cols-3">
            <CapacityGauge
              title="Bed Capacity"
              value={metrics.occupied_beds}
              total={metrics.total_beds}
              percentage={metrics.bed_occupancy}
            />
            <CapacityGauge
              title="ICU Capacity"
              value={metrics.occupied_icu}
              total={metrics.total_icu}
              percentage={metrics.icu_occupancy}
            />
            <CapacityGauge
              title="Ventilators"
              value={metrics.ventilators_used}
              total={metrics.total_ventilators}
              percentage={metrics.ventilator_usage}
            />
          </div>

          {/* Trend Chart */}
          {trendsLoading ? (
            <Skeleton className="h-[350px] w-full rounded-lg" />
          ) : (
            <TrendChart data={trendData} title="30-Day Capacity Trends" />
          )}
        </div>

        {/* Right Column - Side Panel */}
        <div className="space-y-6">
          {/* Risk Assessment */}
          <RiskPanel
            score={risk.score}
            maxScore={risk.max_score}
            level={risk.level}
            factors={risk.factors}
          />

          {/* Environmental Factors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Environmental Factors</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <ThermometerSun className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Temperature</p>
                      <p className="text-xs text-muted-foreground">Current</p>
                    </div>
                  </div>
                  <span className="text-lg font-mono font-semibold">{environment.temperature}°C</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <Droplets className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Humidity</p>
                      <p className="text-xs text-muted-foreground">Current</p>
                    </div>
                  </div>
                  <span className="text-lg font-mono font-semibold">{environment.humidity}%</span>
                </div>

                <div className="p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <Waves className="h-5 w-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">Air Quality</p>
                        <p className="text-xs text-muted-foreground">{dashboardData ? 'Live API' : 'Sample'}</p>
                      </div>
                    </div>
                    <Badge className={aqiLevel.color}>
                      {aqiLevel.label}
                    </Badge>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-mono font-bold">{environment.aqi}</span>
                    <span className="text-xs text-muted-foreground">AQI</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    {environment.aqi > 100 
                      ? "May increase respiratory admissions by 15-20% in next 48 hours"
                      : "Air quality within acceptable range"}
                  </p>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <Activity className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Regional Flu Cases</p>
                      <p className="text-xs text-muted-foreground">Last 7 days</p>
                    </div>
                  </div>
                  <span className="text-lg font-mono font-semibold">{environment.flu_cases.toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
