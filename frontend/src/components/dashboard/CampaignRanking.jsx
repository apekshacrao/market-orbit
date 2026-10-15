import React from 'react';

export default function CampaignRanking({
  topCampaigns = [
    { name: 'Summer Sale', roas: 4.8 },
    { name: 'Festive Offers', roas: 3.9 },
    { name: 'Brand Awareness', roas: 3.2 }
  ],
  bottomCampaigns = [
    { name: 'Winter Promo', roas: 0.8 },
    { name: 'Email Retargeting', roas: 1.1 },
    { name: 'Display Ads', roas: 1.4 }
  ]
}) {
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