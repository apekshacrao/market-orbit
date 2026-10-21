import React from 'react';

const number = (value) => value == null || !Number.isFinite(Number(value))
  ? 'Unavailable'
  : new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(Number(value));

export default function KpiCards({ kpis }) {
  const items = [
    { title: 'Total spend', value: number(kpis?.totalSpend), context: 'Across the selected dataset' },
    { title: 'Total revenue', value: number(kpis?.totalRevenue), context: 'Across the selected dataset' },
    { title: 'Overall ROAS', value: kpis?.overallRoas == null ? 'Unavailable' : `${number(kpis.overallRoas)}×`, context: 'Revenue per unit of spend' },
    { title: 'Conversion rate', value: kpis?.avgConversionRate == null ? 'Unavailable' : `${number(kpis.avgConversionRate)}%`, context: 'Conversions as a share of clicks' },
    { title: 'Average CPA', value: number(kpis?.avgCpa), context: 'Spend per conversion' },
  ];

  return (
    <section className="kpi-grid" aria-label="Dataset key performance indicators">
      {items.map((item) => (
        <article className="kpi-card" key={item.title}>
          <p className="kpi-title">{item.title}</p>
          <h2 className="kpi-value">{item.value}</h2>
          <span className="kpi-context">{item.context}</span>
        </article>
      ))}
    </section>
  );
}
