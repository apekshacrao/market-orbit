import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function PerformanceChart({ data = [] }) {
  const chartData = Array.isArray(data) ? data.slice(0, 10) : [];
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('reduce-motion');
  return <section className="performance-chart-wrapper">
    <h2>Campaign Spend vs Revenue</h2>
    {chartData.length ? <div className="performance-chart">
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 24, left: 0 }}>
          <CartesianGrid stroke="#353C30" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="campaignName" stroke="#AAA99A" angle={-20} textAnchor="end" height={58} interval={0} tick={{ fontSize: 12 }} />
          <YAxis stroke="#AAA99A" tickFormatter={(value) => Number(value).toLocaleString()} />
          <Tooltip contentStyle={{ backgroundColor: '#171B15', border: '1px solid #353C30', borderRadius: '8px', color: '#E7E3D6' }} formatter={(value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })} />
          <Legend />
          <Bar dataKey="spend" name="Spend" fill="#78966A" radius={[4, 4, 0, 0]} isAnimationActive={!reducedMotion} animationDuration={550} />
          <Bar dataKey="revenue" name="Revenue" fill="#C5A15B" radius={[4, 4, 0, 0]} isAnimationActive={!reducedMotion} animationDuration={550} />
        </BarChart>
      </ResponsiveContainer>
    </div> : <p className="empty-state">No campaign performance data is available for this dataset.</p>}
  </section>;
}
