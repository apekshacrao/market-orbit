import React from 'react';

export default function KpiCards({ kpis = {} }) {
  const cards = [
    { label: 'Total Spend', value: kpis.totalSpend || '$0' },
    { label: 'Total Revenue', value: kpis.totalRevenue || '$0' },
    { label: 'Overall ROAS', value: kpis.overallRoas || '0.0x' },
    { label: 'Avg Conversion Rate', value: kpis.avgConversionRate || '0.0%' },
    { label: 'Avg CPA', value: kpis.avgCpa || '$0.00' },
  ];

  return (
    <div className="kpi-cards-grid">
      {cards.map((card, idx) => (
        <div key={idx} className="kpi-card">
          <span className="kpi-label">{card.label}</span>
          <span className="kpi-value">{card.value}</span>
        </div>
      ))}
    </div>
  );
}
