function shortDate(value) {
  if (!value) return '';
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function amount(value) {
  return value == null || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

export default function TrendCharts({ trendData = [], channelData = [] }) {
  const datedRows = trendData.slice(-12);
  const maxTrend = Math.max(1, ...datedRows.flatMap((row) => [Number(row.spend) || 0, Number(row.revenue) || 0]));
  const maxChannel = Math.max(1, ...channelData.map((row) => Number(row.spend) || 0));
  return (
    <section className="trend-grid" aria-label="Channel and time based analytics">
      <article className="panel trend-panel">
        <div className="panel-heading"><div><p className="eyebrow">BY CHANNEL</p><h2>Channel mix</h2></div><span className="panel-icon" aria-hidden="true">⌁</span></div>
        {!channelData.length ? <p className="panel-empty">Channel comparisons are unavailable for this dataset.</p> : <div className="channel-list">
          {channelData.map((channel) => <div className="channel-row" key={channel.channel}>
            <div className="channel-label"><strong>{channel.channel}</strong><span>{amount(channel.conversions)} conversions</span></div>
            <div className="channel-meter"><span style={{ width: `${Math.max(channel.spend > 0 ? 1 : 0, (Number(channel.spend || 0) / maxChannel) * 100)}%` }} /></div>
            <div className="channel-totals"><span>Spend <b>{amount(channel.spend)}</b></span><span>Revenue <b>{amount(channel.revenue)}</b></span></div>
          </div>)}
          <p className="chart-footnote">Spend and revenue use the source dataset currency.</p>
        </div>}
      </article>
      <article className="panel trend-panel">
        <div className="panel-heading"><div><p className="eyebrow">OVER TIME</p><h2>Performance trend</h2></div><span className="panel-icon" aria-hidden="true">◷</span></div>
        {!datedRows.length ? <div className="trend-empty"><span className="trend-empty-mark" aria-hidden="true">—</span><p>No dated records were returned. Add a date column to your CSV to explore performance over time.</p></div> : <>
          <div className="trend-legend"><span><i className="legend-swatch spend-swatch" /> Spend</span><span><i className="legend-swatch revenue-swatch" /> Revenue</span></div>
          <div className="trend-bars" role="img" aria-label="Spend and revenue by date">
            {datedRows.map((row) => <div className="trend-day" key={row.date} title={`${shortDate(row.date)} · Spend ${amount(row.spend)} · Revenue ${amount(row.revenue)}`}>
              <div className="trend-pair"><span className="trend-bar spend-fill" style={{ height: `${Math.max(Number(row.spend) > 0 ? 2 : 0, (Number(row.spend || 0) / maxTrend) * 100)}%` }} /><span className="trend-bar revenue-fill" style={{ height: `${Math.max(Number(row.revenue) > 0 ? 2 : 0, (Number(row.revenue || 0) / maxTrend) * 100)}%` }} /></div>
              <span className="trend-date">{shortDate(row.date)}</span>
            </div>)}
          </div>
        </>}
      </article>
    </section>
  );
}
