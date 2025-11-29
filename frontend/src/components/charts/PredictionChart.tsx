import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart, ReferenceLine } from "recharts";

interface PredictionChartProps {
  data: any[];
  title: string;
  capacityThreshold?: number;
}

export const PredictionChart = ({ data, title, capacityThreshold = 180 }: PredictionChartProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/20" />
            <XAxis 
              dataKey="date" 
              className="text-xs text-muted-foreground"
              tick={{ fill: "currentColor" }}
            />
            <YAxis 
              className="text-xs text-muted-foreground"
              tick={{ fill: "currentColor" }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px"
              }}
            />
            <Legend />
            
            {/* Capacity threshold line */}
            <ReferenceLine 
              y={capacityThreshold} 
              stroke="hsl(var(--critical))" 
              strokeDasharray="5 5"
              label={{ value: "Capacity", fill: "hsl(var(--critical))", fontSize: 12 }}
            />
            
            {/* Confidence interval */}
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill="hsl(var(--primary))"
              fillOpacity={0.1}
              name="Upper Bound"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill="hsl(var(--primary))"
              fillOpacity={0.1}
              name="Lower Bound"
            />
            
            {/* Actual values */}
            <Line 
              type="monotone" 
              dataKey="actual" 
              stroke="hsl(var(--chart-1))" 
              strokeWidth={2}
              name="Historical"
              dot={false}
            />
            
            {/* Predicted values */}
            <Line 
              type="monotone" 
              dataKey="predicted" 
              stroke="hsl(var(--chart-1))" 
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
              dot={{ fill: "hsl(var(--chart-1))", r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
