function formatRoas(value) {
  return value == null || !Number.isFinite(Number(value)) ? 'ROAS unavailable' : `${Number(value).toFixed(2)}× ROAS`;
}

function RankingList({ items, tone, emptyMessage }) {
  if (!items.length) return <p className="panel-empty">{emptyMessage}</p>;
  return <ol className={`ranking-list ${tone}`}>
    {items.map((campaign, index) => (
      <li className="ranking-item" key={`${campaign.campaignName}-${index}`}>
        <span className="ranking-number">{String(index + 1).padStart(2, '0')}</span>
        <span className="ranking-name">{campaign.campaignName || 'Unnamed campaign'}</span>
        <span className="ranking-value">{formatRoas(campaign.roas)}</span>
      </li>
    ))}
  </ol>;
}

export default function CampaignRanking({ topCampaigns = [], bottomCampaigns = [] }) {
  return (
    <section className="campaign-ranking-container" aria-label="Campaign rankings">
      <article className="panel ranking-panel"><div className="panel-heading"><div><p className="eyebrow">LEADING THE WAY</p><h2>Top performers</h2></div><span className="panel-icon positive" aria-hidden="true">↗</span></div><RankingList items={topCampaigns} tone="ranking-positive" emptyMessage="No ranked campaigns are available for this dataset yet." /></article>
      <article className="panel ranking-panel"><div className="panel-heading"><div><p className="eyebrow">ROOM TO OPTIMIZE</p><h2>Needs attention</h2></div><span className="panel-icon caution" aria-hidden="true">⌁</span></div><RankingList items={bottomCampaigns} tone="ranking-caution" emptyMessage="No underperforming campaigns were returned." /></article>
    </section>
  );
}
