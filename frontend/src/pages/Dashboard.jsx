import { useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import CampaignRanking from '../components/dashboard/CampaignRanking';
import KpiCards from '../components/dashboard/KpiCards';
import Loader from '../components/common/Loader';
import ErrorMessage from '../components/common/ErrorMessage';
import { useAnalysis } from '../hooks/useAnalysis';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';

export default function Dashboard({ user }) {
  const workspace = useDatasetWorkspace();
  const [retry, setRetry] = useState(0);
  const { data, loading, error } = useAnalysis(workspace.datasetId, retry);
  const welcome = user?.name || user?.email?.split('@')[0] || 'there';
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}>
    <div className="page-heading dashboard-heading"><div><p className="eyebrow">PERFORMANCE OVERVIEW</p><h1>Good to see you, {welcome}.</h1><p>Your campaign data, brought into focus.</p></div><div className="dashboard-actions"><div className="dataset-picker-wrap"><label htmlFor="dataset-select">ACTIVE DATASET</label><select id="dataset-select" value={workspace.datasetId} onChange={(e) => workspace.selectDataset(e.target.value)} disabled={workspace.loading || !workspace.datasets.length}><option value="">No datasets yet</option>{workspace.datasets.map((d) => <option key={d.id} value={d.id}>{d.filename} · {d.status}</option>)}</select></div><a className="button button-primary button-compact" href="/upload">Upload dataset</a></div></div>
    {workspace.loading && <div className="dashboard-loading"><Loader message="Finding your datasets…" /></div>}
    {!workspace.loading && workspace.error && <div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh} /></div>}
    {!workspace.loading && !workspace.error && !workspace.datasets.length && <section className="panel empty-dashboard"><div className="empty-orbit">◉</div><p className="eyebrow">A FRESH START</p><h2>Your first dataset is the starting point.</h2><p>Upload a CSV with campaign name, channel, spend, and conversions to explore performance.</p><a className="button button-primary" href="/upload">Upload a dataset</a></section>}
    {!workspace.loading && workspace.datasetId && <>
      <div className="results-toolbar"><span>{workspace.selectedDataset?.filename || 'Selected dataset'}</span><button className="text-button" type="button" onClick={() => setRetry((n) => n + 1)} disabled={loading}>Refresh results</button></div>
      {error && <div className="dashboard-feedback"><ErrorMessage message={error} onRetry={() => setRetry((n) => n + 1)} /></div>}
      {!error && <><KpiCards kpis={data?.kpis} loading={loading} />{loading && <div className="analysis-skeleton"><div className="skeleton skeleton-panel" /><div className="skeleton skeleton-panel" /></div>}{data && !loading && <CampaignRanking topCampaigns={data.topCampaigns || []} bottomCampaigns={data.bottomCampaigns || []} />}{!loading && !data && <div className="panel panel-empty">No analysis results were returned for this dataset yet.</div>}</>}
      <section className="overview-links"><a className="panel overview-link" href="/graphs"><span className="panel-icon">⌁</span><strong>Explore graphs &amp; trends</strong><small>Compare campaign and channel performance</small></a><a className="panel overview-link" href="/recommendations"><span className="panel-icon gold">✳</span><strong>AI recommendations</strong><small>Review actions from your analysis</small></a><a className="panel overview-link" href="/live-data"><span className="panel-icon">◉</span><strong>Latest dataset data</strong><small>Inspect the records available now</small></a></section>
    </>}
  </WorkspacePage>;
}
