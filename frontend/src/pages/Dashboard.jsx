import React from 'react';
import KpiCards from '../components/dashboard/KpiCards';
import CampaignRanking from '../components/dashboard/CampaignRanking';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import TrendCharts from '../components/dashboard/TrendCharts';
import AiRecommendations from '../components/dashboard/AiRecommendations';
import { useAnalysis } from '../hooks/useAnalysis';

export default function Dashboard() {
  const { data, loading, error } = useAnalysis();

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div>Error loading analysis: {error}</div>;

  return (
    <div className="page-container dashboard-page">
      <h2>Marketing Performance Dashboard</h2>
      <KpiCards kpis={data?.kpis} />
      <PerformanceChart data={data?.performance} />
      <CampaignRanking topCampaigns={data?.topCampaigns} bottomCampaigns={data?.bottomCampaigns} />
      <TrendCharts trendData={data?.trends} />
      <AiRecommendations recommendations={data?.recommendations} />
    </div>
  );
}
