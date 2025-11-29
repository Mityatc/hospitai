export const sampleDashboardData = {
  hospital: {
    id: "H001",
    name: "City General Hospital",
    location: "Delhi"
  },
  metrics: {
    total_beds: 200,
    occupied_beds: 149,
    bed_occupancy: 74.5,
    total_icu: 30,
    occupied_icu: 22,
    icu_occupancy: 73.3,
    total_ventilators: 20,
    ventilators_used: 11,
    ventilator_usage: 55.0,
    staff_on_duty: 121,
    staff_ratio: 0.81
  },
  risk: {
    score: 3,
    max_score: 6,
    level: "HIGH",
    factors: [
      { name: "Flu Cases", value: 70.1, threshold: 50, triggered: true },
      { name: "Air Quality", value: 132, threshold: 100, triggered: true },
      { name: "Staff Ratio", value: 0.81, threshold: 1.0, triggered: true },
      { name: "Bed Occupancy", value: 74.5, threshold: 80, triggered: false },
      { name: "ICU Occupancy", value: 73.3, threshold: 75, triggered: false },
      { name: "Ventilator Usage", value: 55, threshold: 70, triggered: false }
    ]
  },
  environment: {
    temperature: 10.6,
    humidity: 65,
    aqi: 144,
    flu_cases: 8519
  },
  trends: {
    bed_change_1d: 12,
    bed_change_3d: 24,
    bed_change_7d: 34,
    icu_change_1d: 3,
    direction: "increasing",
    velocity: "moderate"
  },
  timestamp: new Date().toISOString(),
  alerts: [
    {
      id: 1,
      severity: "warning",
      message: "ICU at 85% capacity - 4 beds remaining",
      timestamp: new Date().toISOString()
    }
  ]
};

export const trendData = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  beds: Math.floor(120 + Math.random() * 40 + i * 0.5),
  icu: Math.floor(15 + Math.random() * 10 + i * 0.2),
  admissions: Math.floor(8 + Math.random() * 6),
  discharges: Math.floor(6 + Math.random() * 5)
}));

export const predictionData = Array.from({ length: 37 }, (_, i) => {
  const isPrediction = i >= 30;
  const baseValue = 149 + (i - 30) * 2.5;
  return {
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    actual: !isPrediction ? Math.floor(120 + Math.random() * 40 + i * 0.8) : null,
    predicted: isPrediction ? Math.floor(baseValue + Math.random() * 10) : null,
    upperBound: isPrediction ? Math.floor(baseValue + 15) : null,
    lowerBound: isPrediction ? Math.floor(baseValue - 10) : null
  };
});

export const aiRecommendations = [
  {
    id: 1,
    priority: 5,
    title: "Activate ambulance diversion",
    type: "DIVERSION",
    autoExecute: false,
    status: "pending",
    confidence: 92,
    reasoning: "ICU capacity at critical threshold. Diverting non-critical cases will prevent overcrowding."
  },
  {
    id: 2,
    priority: 4,
    title: "Request emergency staff callback",
    type: "STAFF_CALL",
    autoExecute: false,
    status: "pending",
    confidence: 88,
    reasoning: "Staff ratio below minimum safe threshold. Additional personnel needed for adequate patient care."
  },
  {
    id: 3,
    priority: 3,
    title: "Alert bed management team",
    type: "ALERT",
    autoExecute: true,
    status: "executed",
    confidence: 95,
    executedAt: "14:32",
    reasoning: "Proactive notification to prepare for discharge planning and bed turnover optimization."
  }
];
