import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface TrendChartProps {
  data: any[];
  title: string;
}

export const TrendChart = ({ data, title }: TrendChartProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
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
            <Line 
              type="monotone" 
              dataKey="beds" 
              stroke="hsl(var(--chart-1))" 
              strokeWidth={2}
              name="Bed Occupancy"
            />
            <Line 
              type="monotone" 
              dataKey="icu" 
              stroke="hsl(var(--chart-2))" 
              strokeWidth={2}
              name="ICU"
            />
            <Line 
              type="monotone" 
              dataKey="admissions" 
              stroke="hsl(var(--chart-3))" 
              strokeWidth={2}
              name="Admissions"
            />
            <Line 
              type="monotone" 
              dataKey="discharges" 
              stroke="hsl(var(--chart-4))" 
              strokeWidth={2}
              name="Discharges"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
