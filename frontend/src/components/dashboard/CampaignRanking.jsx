import React from 'react';

function RankingList({ title, campaigns, variant }) {
  return (
    <section className="ranking-column">
      <h3>{title}</h3>
      {campaigns.length ? (
        <ul>{campaigns.map((campaign, index) => (
          <li key={`${campaign.campaignName}-${index}`} className={`ranking-item ${variant}`}>
            <span>{campaign.campaignName}</span>
            <span>{campaign.roas == null ? 'ROAS unavailable' : `ROAS: ${Number(campaign.roas).toFixed(2)}x`}</span>
          </li>
        ))}</ul>
      ) : <p className="empty-state">No campaign ranking data is available.</p>}
    </section>
  );
}

export default function CampaignRanking({ topCampaigns = [], bottomCampaigns = [] }) {
  return (
    <div className="campaign-ranking-container">
      <RankingList title="Top Performing Campaigns" campaigns={topCampaigns} variant="top" />
      <RankingList title="Underperforming Campaigns" campaigns={bottomCampaigns} variant="bottom" />
    </div>
  );
}
