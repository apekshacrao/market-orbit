import React from 'react';

export default function CampaignRanking({ topCampaigns = [], bottomCampaigns = [] }) {
  return (
    <div className="campaign-ranking-container">
      <div className="ranking-column">
        <h3>Top Performing Campaigns</h3>
        <ul>
          {topCampaigns.map((c, i) => (
            <li key={i} className="ranking-item top">
              <span>{c.name}</span>
              <span>ROAS: {c.roas}x</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="ranking-column">
        <h3>Underperforming Campaigns</h3>
        <ul>
          {bottomCampaigns.map((c, i) => (
            <li key={i} className="ranking-item bottom">
              <span>{c.name}</span>
              <span>ROAS: {c.roas}x</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
