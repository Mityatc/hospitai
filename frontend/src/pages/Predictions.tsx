import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PredictionChart } from "@/components/charts/PredictionChart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Calendar, TrendingUp, AlertCircle, Download, RefreshCw } from "lucide-react";
import { usePredictions } from "@/hooks/useApi";
import { useState } from "react";

export default function Predictions() {
  const [forecastDays, setForecastDays] = useState([7]);
  
  const { data: predictionsData, isLoading, error, refetch } = usePredictions('H001', forecastDays[0]);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "Low": return "bg-success text-success-foreground";
      case "Medium": return "bg-warning text-warning-foreground";
      case "High": return "bg-critical text-critical-foreground";
      case "Critical": return "bg-emergency text-emergency-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  // Transform data for the chart
  const chartData = predictionsData?.data || [];
  const insights = predictionsData?.insights;

  // Build forecast table from predictions
  const forecastTable = chartData
    .filter(d => d.predicted !== null)
    .map(d => ({
      date: d.date,
      predicted: d.predicted!,
      confidence: `±${d.upper_bound && d.predicted ? d.upper_bound - d.predicted : 10}`,
      risk: d.risk_level || 'Medium'
    }));

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        <Skeleton className="h-[100px] w-full rounded-lg" />
        <Skeleton className="h-[400px] w-full rounded-lg" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-[120px] rounded-lg" />
          <Skeleton className="h-[120px] rounded-lg" />
          <Skeleton className="h-[120px] rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Capacity Predictions</h1>
          <p className="text-muted-foreground mt-1">
            AI-powered forecast for next {forecastDays[0]} days
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-warning/10 border border-warning/30 text-warning">
          <p className="text-sm">⚠️ Could not load predictions from API. Please check if the backend is running.</p>
        </div>
      )}

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Forecast Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="forecast-days">Prediction Horizon</Label>
              <span className="text-sm font-medium">{forecastDays[0]} days</span>
            </div>
            <Slider
              id="forecast-days"
              min={1}
              max={14}
              step={1}
              value={forecastDays}
              onValueChange={(value) => {
                setForecastDays(value);
              }}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Longer forecasts have wider confidence intervals
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Forecast Chart */}
      <PredictionChart
        data={chartData}
        title="Bed Occupancy Forecast with Confidence Intervals"
        capacityThreshold={insights?.threshold || 180}
      />

      {/* Key Insights */}
      {insights && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-critical/30 bg-critical/5">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-critical/20">
                  <TrendingUp className="h-5 w-5 text-critical" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Peak Occupancy</p>
                  <p className="text-2xl font-bold font-mono mt-1">{insights.peak_occupancy} beds</p>
                  <p className="text-xs text-muted-foreground mt-1">Expected on {insights.peak_date}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-warning/30 bg-warning/5">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-warning/20">
                  <Calendar className="h-5 w-5 text-warning" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Days Until Threshold</p>
                  <p className="text-2xl font-bold font-mono mt-1">
                    {insights.days_until_threshold !== null ? `${insights.days_until_threshold} days` : 'N/A'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Capacity limit: {insights.threshold}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/20">
                  <AlertCircle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Recommended Action</p>
                  <p className="text-sm font-semibold mt-1">{insights.recommendation}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {insights.peak_occupancy > insights.threshold * 0.9 ? 'Add 20-30 beds' : 'Continue monitoring'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Forecast Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Detailed Forecast</CardTitle>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {forecastTable.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              <p>No forecast data available. Try adjusting the prediction horizon.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Predicted Beds</th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Confidence</th>
                    <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastTable.map((row, idx) => (
                    <tr key={idx} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 font-medium">{row.date}</td>
                      <td className="py-3 px-4 font-mono font-semibold">{row.predicted}</td>
                      <td className="py-3 px-4 font-mono text-sm text-muted-foreground">{row.confidence}</td>
                      <td className="py-3 px-4">
                        <Badge className={getRiskColor(row.risk)}>
                          {row.risk}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Model Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">About the Prediction Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="p-4 rounded-lg bg-muted/50">
              <h4 className="font-medium mb-2">Model Type</h4>
              <p className="text-sm text-muted-foreground">
                Linear Regression with seasonal adjustments and environmental factors
              </p>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <h4 className="font-medium mb-2">Input Features</h4>
              <p className="text-sm text-muted-foreground">
                Historical occupancy, flu cases, air quality, temperature, day of week
              </p>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <h4 className="font-medium mb-2">Training Data</h4>
              <p className="text-sm text-muted-foreground">
                Last 30 days of hospital data with hourly granularity
              </p>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <h4 className="font-medium mb-2">Confidence Intervals</h4>
              <p className="text-sm text-muted-foreground">
                Based on historical prediction error and forecast horizon
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
