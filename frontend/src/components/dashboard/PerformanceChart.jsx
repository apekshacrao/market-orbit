import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const sampleData = [
  { date: 'Mon', spend: 1200, revenue: 3200 },
  { date: 'Tue', spend: 1500, revenue: 4100 },
  { date: 'Wed', spend: 1100, revenue: 2900 },
  { date: 'Thu', spend: 1800, revenue: 5200 },
  { date: 'Fri', spend: 1600, revenue: 4700 },
  { date: 'Sat', spend: 2100, revenue: 6100 },
  { date: 'Sun', spend: 1700, revenue: 5400 }
];

export default function PerformanceChart({ data }) {
  const chartData = data?.length ? data : sampleData;

  return (
    <div className="performance-chart-wrapper">
      <h3>Campaign Performance Overview</h3>

      <div className="performance-chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid stroke="#36315B" strokeDasharray="3 3" />

            <XAxis
              dataKey="date"
              stroke="#B8B2D0"
            />

            <YAxis
              stroke="#B8B2D0"
            />

            <Tooltip
              contentStyle={{
                backgroundColor: '#080B38',
                border: '1px solid #512777',
                borderRadius: '8px',
                color: '#F5F3FA'
              }}
            />

            <Legend />

            <Line
              type="monotone"
              dataKey="spend"
              name="Spend"
              stroke="#9B72CF"
              strokeWidth={3}
              dot={false}
            />

            <Line
              type="monotone"
              dataKey="revenue"
              name="Revenue"
              stroke="#52B7D8"
              strokeWidth={3}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}