import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import chartTheme, { chartAxisStyle, chartTooltipStyle } from './chartTheme';

export default function PerformanceChart({ data = [] }) {
  const chartData = Array.isArray(data) ? [...data].sort((a, b) => Number(b.spend || 0) - Number(a.spend || 0)).slice(0, 10) : [];
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('reduce-motion');
  return <section className="performance-chart-wrapper">
    <h2>Campaign Spend vs Revenue</h2>
    <p className="chart-summary" id="campaign-performance-summary">{data.length > 10 ? `Top 10 of ${data.length} campaigns by spend. ` : ''}Amounts use dataset units; currency is not provided.</p>
    {chartData.length ? <div className="performance-chart" role="group" aria-label="Campaign spend and revenue bar chart" aria-describedby="campaign-performance-summary">
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 24, left: 0 }}>
          <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="campaignName" stroke={chartTheme.muted} angle={-20} textAnchor="end" height={58} interval={0} tick={{ fontSize: 12, fill: chartTheme.muted }} />
          <YAxis stroke={chartTheme.muted} tick={{ fill: chartTheme.muted, fontSize: chartAxisStyle.fontSize }} tickFormatter={(value) => Number(value).toLocaleString('en-IN')} />
          <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} />
          <Legend wrapperStyle={{ color: chartTheme.muted }} />
          <Bar dataKey="spend" name="Spend" fill={chartTheme.series.spend} radius={[4, 4, 0, 0]} isAnimationActive={!reducedMotion} animationDuration={550} />
          <Bar dataKey="revenue" name="Revenue" fill={chartTheme.series.revenue} radius={[4, 4, 0, 0]} isAnimationActive={!reducedMotion} animationDuration={550} />
        </BarChart>
      </ResponsiveContainer>
    </div> : <p className="empty-state">No campaign performance data is available for this dataset.</p>}
    {chartData.length > 0 && <details className="chart-data-details"><summary>View values for plotted campaigns</summary><div className="forecast-table-wrap"><table className="forecast-table"><caption className="visually-hidden">Campaign spend, revenue, and return on ad spend for the campaigns shown in the chart</caption><thead><tr><th>Campaign</th><th>Spend</th><th>Revenue</th><th>ROAS</th></tr></thead><tbody>{chartData.map((item) => <tr key={item.campaignName}><td>{item.campaignName}</td><td>{Number(item.spend).toLocaleString('en-IN')}</td><td>{item.revenue == null ? 'Unavailable' : Number(item.revenue).toLocaleString('en-IN')}</td><td>{item.roas == null ? 'Unavailable' : `${Number(item.roas).toFixed(2)}×`}</td></tr>)}</tbody></table></div></details>}
  </section>;
}
