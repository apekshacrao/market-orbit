const metrics = [
  { key: 'totalSpend', label: 'Total spend', icon: '↗', format: (value) => formatAmount(value), note: 'Across this dataset' },
  { key: 'totalRevenue', label: 'Total revenue', icon: '◈', format: (value) => formatAmount(value), note: 'Reported by dataset' },
  { key: 'overallRoas', label: 'Overall ROAS', icon: '◎', format: (value) => `${formatDecimal(value)}×`, note: 'Revenue per spend' },
  { key: 'avgConversionRate', label: 'Conversion rate', icon: '⌁', format: (value) => `${formatDecimal(value)}%`, note: 'Conversions per click' },
  { key: 'avgCpa', label: 'Average CPA', icon: '◌', format: (value) => formatAmount(value), note: 'Spend per conversion' },
];

function formatAmount(value) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value));
}

function formatDecimal(value) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function KpiCards({ kpis = {}, loading = false }) {
  return (
    <section className="kpi-cards-grid" aria-label="Key performance indicators">
      {metrics.map((metric, index) => (
        <article className="kpi-card" key={metric.key} style={{ '--stagger': `${index * 55}ms` }}>
          <div className="kpi-card-top"><span className="kpi-label">{metric.label}</span><span className="kpi-icon" aria-hidden="true">{metric.icon}</span></div>
          {loading ? <div className="skeleton kpi-skeleton" /> : <strong className="kpi-value">{kpis[metric.key] == null ? 'Not available' : metric.format(kpis[metric.key])}</strong>}
          <span className="kpi-note">{metric.note}{['totalSpend', 'totalRevenue', 'avgCpa'].includes(metric.key) && <span className="unit-note"> · data currency</span>}</span>
        </article>
      ))}
    </section>
  );
}
