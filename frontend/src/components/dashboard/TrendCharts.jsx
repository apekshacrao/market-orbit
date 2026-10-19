import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function TrendCharts({ data = [] }) {
  return (
    <section className="trend-charts-wrapper">
      <h3>Daily Trends</h3>
      {data.length ? (
        <div className="trend-chart">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid stroke="#36315B" strokeDasharray="3 3" />
              <XAxis dataKey="date" stroke="#B8B2D0" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="metrics" stroke="#B8B2D0" />
              <YAxis yAxisId="conversions" orientation="right" stroke="#B8B2D0" />
              <Tooltip contentStyle={{ backgroundColor: '#080B38', border: '1px solid #512777', borderRadius: '8px', color: '#F5F3FA' }} />
              <Legend />
              <Line yAxisId="metrics" type="monotone" dataKey="spend" name="Spend" stroke="#9B72CF" strokeWidth={3} dot={false} />
              <Line yAxisId="metrics" type="monotone" dataKey="revenue" name="Revenue" stroke="#52B7D8" strokeWidth={3} dot={false} connectNulls={false} />
              <Line yAxisId="conversions" type="monotone" dataKey="conversions" name="Conversions" stroke="#5ed39a" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : <p className="empty-state">No trend data is available for this dataset.</p>}
    </section>
  );
}
