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

export default function PerformanceChart({ data }) {
  const chartData = data || [];

  return (
    <div className="performance-chart-wrapper">
      <h3>Daily Performance</h3>

      {chartData.length ? <div className="performance-chart">
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
      </div> : <p className="empty-state">No dated performance data is available for this dataset.</p>}
    </div>
  );
}
