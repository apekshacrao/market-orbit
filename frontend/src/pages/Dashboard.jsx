import React from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import CampaignRanking from '../components/dashboard/CampaignRanking';
import KpiCards from '../components/dashboard/KpiCards';
import TrendCharts from '../components/dashboard/TrendCharts';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import AiRecommendations from '../components/dashboard/AiRecommendations';

export default function Dashboard() {
  const topCampaigns = [
    { name: 'Summer Sale', roas: 3.6 },
    { name: 'Diwali Campaign', roas: 3.0 },
    { name: 'Product Launch', roas: 2.3 }
  ];

  const bottomCampaigns = [
    { name: 'Winter Sale', roas: 0.8 },
    { name: 'Email Campaign', roas: 1.1 },
    { name: 'Social Campaign', roas: 1.3 }
  ];

  return (
  <div className="dashboard-page">
    <Navbar />

    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-content">
        <h1>Dashboard</h1>
        <p>Welcome to your marketing performance dashboard.</p>
        <KpiCards />
<CampaignRanking
  topCampaigns={topCampaigns}
  bottomCampaigns={bottomCampaigns}
/>
<PerformanceChart />
<TrendCharts />
<AiRecommendations />

      </main>
    </div>
  </div>
);

 
}