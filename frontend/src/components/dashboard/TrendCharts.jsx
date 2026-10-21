import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import chartTheme, { chartTooltipStyle } from './chartTheme';

export default function TrendCharts({ data = [] }) {
  return (
    <section className="trend-charts-wrapper">
      <h3>Daily Trends</h3>
      {data.length ? (
        <>
        <p className="chart-summary" id="daily-trends-summary">Spend and revenue use the left axis; conversions use the right axis. Monetary amounts use dataset units because currency is not provided.</p>
        <div className="trend-chart" role="group" aria-label="Daily marketing metrics trend chart" aria-describedby="daily-trends-summary">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
              <XAxis dataKey="date" stroke={chartTheme.muted} tick={{ fontSize: 12, fill: chartTheme.muted }} />
              <YAxis yAxisId="metrics" stroke={chartTheme.muted} tick={{ fill: chartTheme.muted }} />
              <YAxis yAxisId="conversions" orientation="right" stroke={chartTheme.muted} tick={{ fill: chartTheme.muted }} />
              <Tooltip contentStyle={chartTooltipStyle} />
              <Legend wrapperStyle={{ color: chartTheme.muted }} />
              <Line yAxisId="metrics" type="monotone" dataKey="spend" name="Spend" stroke={chartTheme.series.spend} strokeWidth={3} dot={false} />
              <Line yAxisId="metrics" type="monotone" dataKey="revenue" name="Revenue" stroke={chartTheme.series.revenue} strokeWidth={3} dot={false} connectNulls={false} />
              <Line yAxisId="conversions" type="monotone" dataKey="conversions" name="Conversions" stroke={chartTheme.series.conversions} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        </>
      ) : <p className="empty-state">No trend data is available for this dataset.</p>}
    </section>
  );
}
