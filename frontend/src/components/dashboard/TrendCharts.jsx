import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function TrendCharts({ performance = [] }) {
  return (
    <section className="trend-charts-wrapper">
      <h3>Campaign Spend &amp; Revenue</h3>
      {performance.length ? (
        <div className="trend-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performance}>
              <CartesianGrid stroke="#36315B" strokeDasharray="3 3" />
              <XAxis dataKey="campaignName" stroke="#B8B2D0" tick={{ fontSize: 12 }} />
              <YAxis stroke="#B8B2D0" />
              <Tooltip contentStyle={{ backgroundColor: '#080B38', border: '1px solid #512777', borderRadius: '8px', color: '#F5F3FA' }} />
              <Legend />
              <Bar dataKey="spend" name="Spend" fill="#9B72CF" radius={[5, 5, 0, 0]} />
              <Bar dataKey="revenue" name="Revenue" fill="#52B7D8" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : <p className="empty-state">No campaign performance data is available.</p>}
    </section>
  );
}
