import React from 'react';

const number = (value) => value == null || !Number.isFinite(Number(value))
  ? '—'
  : new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(Number(value));

export default function KpiCards({ kpis }) {
  const items = [
    { title: 'Total Spend', value: number(kpis?.totalSpend) },
    { title: 'Total Revenue', value: number(kpis?.totalRevenue) },
    { title: 'Overall ROAS', value: kpis?.overallRoas == null ? '—' : `${number(kpis.overallRoas)}x` },
    { title: 'Conversion Rate', value: kpis?.avgConversionRate == null ? '—' : `${number(kpis.avgConversionRate)}%` },
    { title: 'Average CPA', value: number(kpis?.avgCpa) },
  ];

  return (
    <section className="kpi-grid" aria-label="Dataset key performance indicators">
      {items.map((item) => (
        <article className="kpi-card" key={item.title}>
          <p className="kpi-title">{item.title}</p>
          <h2 className="kpi-value">{item.value}</h2>
          <span className="kpi-change">Dataset results</span>
        </article>
      ))}
    </section>
  );
}
