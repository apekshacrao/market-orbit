function amount(value) {
  return value == null || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 });
}

export default function PerformanceChart({ data = [] }) {
  const rows = data.slice(0, 7);
  const maxValue = Math.max(1, ...rows.flatMap((item) => [Number(item.spend) || 0, Number(item.revenue) || 0]));
  const roasRows = rows.filter((item) => item.roas != null && Number.isFinite(Number(item.roas)));
  const maxRoas = Math.max(1, ...roasRows.map((item) => Number(item.roas)));
  return (
    <section className="panel performance-panel">
      <div className="panel-heading chart-heading"><div><p className="eyebrow">CAMPAIGN MIX</p><h2>Spend &amp; revenue</h2><p className="panel-subtitle">Compare reported spend against revenue for each campaign.</p></div><div className="chart-legend"><span><i className="legend-swatch spend-swatch" /> Spend</span><span><i className="legend-swatch revenue-swatch" /> Revenue</span></div></div>
      {!rows.length ? <p className="panel-empty chart-empty">Campaign performance will appear when this dataset has results.</p> : <div className="bar-chart" role="img" aria-label="Campaign spend and revenue comparison">
        {rows.map((item, index) => <div className="bar-row" key={`${item.campaignName}-${index}`}>
          <div className="bar-label" title={item.campaignName}>{item.campaignName || 'Unnamed campaign'}</div>
          <div className="bar-stack"><div className="bar-line"><span className="bar-track"><span className="bar-fill spend-fill" style={{ width: `${Math.max(item.spend > 0 ? 1 : 0, (Number(item.spend || 0) / maxValue) * 100)}%` }} /></span><span className="bar-value">{amount(item.spend)}</span></div>
            <div className="bar-line"><span className="bar-track"><span className="bar-fill revenue-fill" style={{ width: `${Math.max(item.revenue > 0 ? 1 : 0, (Number(item.revenue || 0) / maxValue) * 100)}%` }} /></span><span className="bar-value">{amount(item.revenue)}</span></div></div>
        </div>)}
      </div>}
      {roasRows.length > 0 && <div className="roas-comparison"><div className="roas-heading"><span className="eyebrow">EFFICIENCY</span><strong>ROAS by campaign</strong></div><div className="roas-list">{roasRows.map((item, index) => <div className="roas-row" key={`${item.campaignName}-roas-${index}`}><span title={item.campaignName}>{item.campaignName}</span><span className="roas-track"><i style={{ width: `${Math.max(Number(item.roas) > 0 ? 2 : 0, (Number(item.roas) / maxRoas) * 100)}%` }} /></span><b>{Number(item.roas).toFixed(2)}×</b></div>)}</div></div>}
      <p className="chart-footnote">Values use the dataset’s original currency; the currency code is not provided by the API.</p>
    </section>
  );
}
