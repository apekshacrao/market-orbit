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
              <CartesianGrid stroke="#353C30" strokeDasharray="3 3" />
              <XAxis dataKey="date" stroke="#AAA99A" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="metrics" stroke="#AAA99A" />
              <YAxis yAxisId="conversions" orientation="right" stroke="#AAA99A" />
              <Tooltip contentStyle={{ backgroundColor: '#171B15', border: '1px solid #353C30', borderRadius: '8px', color: '#E7E3D6' }} />
              <Legend />
              <Line yAxisId="metrics" type="monotone" dataKey="spend" name="Spend" stroke="#78966A" strokeWidth={3} dot={false} />
              <Line yAxisId="metrics" type="monotone" dataKey="revenue" name="Revenue" stroke="#C5A15B" strokeWidth={3} dot={false} connectNulls={false} />
              <Line yAxisId="conversions" type="monotone" dataKey="conversions" name="Conversions" stroke="#8BB58A" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : <p className="empty-state">No trend data is available for this dataset.</p>}
    </section>
  );
}
