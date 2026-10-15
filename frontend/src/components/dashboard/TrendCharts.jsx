import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const sampleTrends = [
  { channel: 'Social', customers: 120, conversions: 35 },
  { channel: 'Search', customers: 180, conversions: 60 },
  { channel: 'Email', customers: 95, conversions: 42 },
  { channel: 'Display', customers: 75, conversions: 20 },
  { channel: 'Referral', customers: 140, conversions: 48 }
];

export default function TrendCharts({ trendData }) {
  const chartData = trendData?.length ? trendData : sampleTrends;

  return (
    <div className="trend-charts-wrapper">
      <h3>Customer &amp; Channel Trends</h3>

      <div className="trend-chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid
              stroke="#36315B"
              strokeDasharray="3 3"
            />

            <XAxis dataKey="channel" stroke="#B8B2D0" />
            <YAxis stroke="#B8B2D0" />

            <Tooltip
              contentStyle={{
                backgroundColor: '#080B38',
                border: '1px solid #512777',
                borderRadius: '8px',
                color: '#F5F3FA'
              }}
            />

            <Legend />

            <Bar
              dataKey="customers"
              name="Customers"
              fill="#512777"
              radius={[5, 5, 0, 0]}
            />

            <Bar
              dataKey="conversions"
              name="Conversions"
              fill="#52B7D8"
              radius={[5, 5, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}