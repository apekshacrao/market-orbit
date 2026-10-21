import React, { useEffect, useState } from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar, { NavIcon } from '../components/common/Sidebar';
import CampaignRanking from '../components/dashboard/CampaignRanking';
import KpiCards from '../components/dashboard/KpiCards';
import Loader from '../components/common/Loader';
import { useAnalysis } from '../hooks/useAnalysis';
import uploadApi from '../api/uploadApi';

export default function Dashboard({ user }) {
  const queryDatasetId = new URLSearchParams(window.location.search).get('dataset_id');
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState(queryDatasetId || localStorage.getItem('dataset_id') || '');
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [datasetsError, setDatasetsError] = useState('');
  const [retry, setRetry] = useState(0);
  const { data, loading, error } = useAnalysis(datasetId, retry);

  useEffect(() => {
    let active = true;
    setDatasetsLoading(true);
    setDatasetsError('');
    uploadApi.getDatasets()
      .then((items) => {
        if (!active) return;
        const available = Array.isArray(items) ? items : [];
        setDatasets(available);
        const currentSelectionExists = available.some((dataset) => dataset.id === datasetId);
        const requestedId = currentSelectionExists ? datasetId : (queryDatasetId || localStorage.getItem('dataset_id'));
        if (requestedId && available.some((dataset) => dataset.id === requestedId)) setDatasetId(requestedId);
        else if (available.length) setDatasetId((current) => available.some((dataset) => dataset.id === current) ? current : available[0].id);
        else setDatasetId('');
      })
      .catch((requestError) => { if (active) setDatasetsError(requestError.message || 'Could not load datasets.'); })
      .finally(() => { if (active) setDatasetsLoading(false); });
    return () => { active = false; };
  }, [retry, queryDatasetId]);

  useEffect(() => {
    if (datasetId) localStorage.setItem('dataset_id', datasetId);
  }, [datasetId]);

  const selectDataset = (event) => {
    const id = event.target.value;
    setDatasetId(id);
    if (id) localStorage.setItem('dataset_id', id);
    else localStorage.removeItem('dataset_id');
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('dataset_id', id);
    else url.searchParams.delete('dataset_id');
    window.history.replaceState({}, '', url);
  };
  const selectedDataset = datasets.find((dataset) => dataset.id === datasetId);
  const trendDates = (data?.trends || []).map((row) => row.date).filter((date) => typeof date === 'string').sort();
  const dateLabel = (date) => new Date(`${date}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

  return <div className="dashboard-page">
    <Navbar user={user} datasetName={selectedDataset?.filename} />
    <div className="dashboard-layout">
      <Sidebar user={user} />
      <main className="dashboard-content">
        <div className="dashboard-heading-row">
          <div><p className="section-kicker">PERFORMANCE OVERVIEW</p><h1>Dashboard</h1><p>Your marketing performance at a glance.</p></div>
          <div className="dashboard-controls">
            <div className="dataset-picker"><label htmlFor="dataset-select">Selected dataset</label><select id="dataset-select" value={datasetId} onChange={selectDataset} disabled={datasetsLoading || !datasets.length}>
              {!datasets.length && <option value="">No datasets yet</option>}
              {datasets.map((dataset) => <option value={dataset.id} key={dataset.id}>{dataset.filename}</option>)}
            </select></div>
            <button className="secondary-button" type="button" onClick={() => setRetry((value) => value + 1)} disabled={loading || datasetsLoading}>{loading ? 'Refreshing…' : 'Refresh analysis'}</button>
            <a className="primary-link-button" href="/upload">Upload Dataset</a>
          </div>
        </div>

        {datasetsLoading && <Loader message="Loading your datasets…" />}
        {!datasetsLoading && datasetsError && <div className="error-message-box" role="alert"><p>{datasetsError}</p><button type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button></div>}
        {!datasetsLoading && !datasetsError && !datasets.length && <section className="empty-panel"><h2>No datasets yet</h2><p>Upload a CSV file to see your campaign KPIs and performance summary.</p><a className="primary-link-button" href="/upload">Upload Dataset</a></section>}
        {datasetId && loading && <div className="dashboard-kpi-skeleton" role="status" aria-label="Loading dashboard metrics">{Array.from({ length: 5 }, (_, index) => <div className="kpi-card" key={index}><span className="skeleton-line skeleton-label"/><span className="skeleton-line skeleton-value"/></div>)}</div>}
        {datasetId && error && <div className="error-message-box" role="alert"><p>Could not load this dataset’s results: {error}</p><button type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button></div>}
        {data && !loading && !error && <>
          <div className="data-source-note"><span className="data-source-status" aria-hidden="true"/><span>Showing <strong>{selectedDataset?.filename || 'selected dataset'}</strong>{trendDates.length > 0 && <> · {trendDates.length} dated records, {dateLabel(trendDates[0])}–{dateLabel(trendDates[trendDates.length - 1])}</>}.</span><small>Amounts use dataset units; currency was not specified.</small></div>
          <KpiCards kpis={data.kpis} />
          <CampaignRanking topCampaigns={(data.topCampaigns || []).slice(0, 4)} bottomCampaigns={(data.bottomCampaigns || []).slice(0, 4)} />
          <p className="dashboard-detail-link"><a href="/graphs">Explore detailed campaign analytics <span aria-hidden="true">→</span></a></p>
        </>}
        {!datasetsLoading && !datasetsError && datasetId && !loading && !error && !data && <div className="empty-panel"><p>No analysis results are available for this dataset yet.</p></div>}
        <nav className="dashboard-shortcuts" aria-label="Explore workspace sections">
          <a href="/graphs"><span className="shortcut-icon" aria-hidden="true"><NavIcon name="chart"/></span><span><strong>Graphs &amp; Trends</strong><small>Explore campaign performance</small></span></a>
          <a href="/recommendations"><span className="shortcut-icon" aria-hidden="true"><NavIcon name="spark"/></span><span><strong>AI Recommendations</strong><small>Review analysis suggestions</small></span></a>
          <a href="/live-data"><span className="shortcut-icon" aria-hidden="true"><NavIcon name="table"/></span><span><strong>Dataset Records</strong><small>Inspect uploaded campaign rows</small></span></a>
        </nav>
      </main>
    </div>
  </div>;
}
