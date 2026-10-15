import React from 'react';

const sampleKpis = [
  { title: 'Total Spend', value: '₹1,25,000', change: '+8.2%' },
  { title: 'Total Revenue', value: '₹3,75,000', change: '+12.5%' },
  { title: 'Overall ROAS', value: '3.0x', change: '+5.4%' },
  { title: 'Conversion Rate', value: '4.8%', change: '+1.2%' },
  { title: 'Average CPA', value: '₹250', change: '-6.3%' },
];

export default function KpiCards() {
  return (
    <section className="kpi-grid">
      {sampleKpis.map((kpi) => (
        <article className="kpi-card" key={kpi.title}>
          <p className="kpi-title">{kpi.title}</p>
          <h2 className="kpi-value">{kpi.value}</h2>
          <span className="kpi-change">{kpi.change} vs previous period</span>
        </article>
      ))}
    </section>
  );
}