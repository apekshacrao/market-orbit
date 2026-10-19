import React, { useEffect, useState } from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import CampaignRanking from '../components/dashboard/CampaignRanking';
import KpiCards from '../components/dashboard/KpiCards';
import TrendCharts from '../components/dashboard/TrendCharts';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import AiRecommendations from '../components/dashboard/AiRecommendations';
import Loader from '../components/common/Loader';
import { useAnalysis } from '../hooks/useAnalysis';
import uploadApi from '../api/uploadApi';

export default function Dashboard({ user }) {
  const queryDatasetId = new URLSearchParams(window.location.search).get('dataset_id');
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState(queryDatasetId || localStorage.getItem('dataset_id') || '');
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [datasetsError, setDatasetsError] = useState(null);
  const { data, loading, error } = useAnalysis(datasetId);

  useEffect(() => {
    let active = true;
    uploadApi.getDatasets()
      .then((items) => {
        if (!active) return;
        setDatasets(items);
        const requestedId = queryDatasetId || localStorage.getItem('dataset_id');
        const validRequestedId = requestedId && items.some((dataset) => dataset.id === requestedId);
        if (!validRequestedId && !queryDatasetId && items.length) setDatasetId(items[0].id);
      })
      .catch((err) => { if (active) setDatasetsError(err.message); })
      .finally(() => { if (active) setDatasetsLoading(false); });
    return () => { active = false; };
  }, []);

  const chooseDataset = (event) => {
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
  const displayName = user?.name || user?.email || 'your workspace';

  return (
    <div className="dashboard-page">
      <Navbar user={user} />
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-content">
          <div className="dashboard-heading-row">
            <div>
              <h1>Dashboard</h1>
              <p>Welcome, {displayName}. Review performance from your uploaded datasets.</p>
            </div>
            <div className="dataset-picker">
              <label htmlFor="dataset-select">Dataset</label>
              <select id="dataset-select" value={datasetId} onChange={chooseDataset} disabled={datasetsLoading || !datasets.length}>
                {!datasets.length && <option value="">No datasets yet</option>}
                {datasets.map((dataset) => <option value={dataset.id} key={dataset.id}>{dataset.filename} · {dataset.status}</option>)}
              </select>
            </div>
          </div>

          {datasetsLoading && <Loader message="Loading your datasets…" />}
          {datasetsError && <div className="error-message-box" role="alert"><p>{datasetsError}</p><button type="button" onClick={() => window.location.reload()}>Retry</button></div>}
          {!datasetsLoading && !datasetsError && datasets.length === 0 && (
            <section className="empty-panel">
              <h2>No datasets yet</h2>
              <p>Upload a CSV file to see its KPIs, campaign rankings, and recommendations here.</p>
              <a className="primary-link-button" href="/upload">Upload dataset</a>
            </section>
          )}
          {datasetId && loading && <Loader message="Loading analysis results…" />}
          {datasetId && error && <div className="error-message-box" role="alert"><p>Could not load this dataset’s results: {error}</p><button type="button" onClick={() => window.location.reload()}>Retry</button></div>}
          {data && !loading && (
            <>
              <p className="data-source-note">Showing results for {selectedDataset?.filename || 'selected dataset'}.</p>
              <KpiCards kpis={data.kpis} />
              <CampaignRanking topCampaigns={data.topCampaigns || []} bottomCampaigns={data.bottomCampaigns || []} />
              <PerformanceChart data={data.performance || []} />
              <TrendCharts data={data.trends || []} />
              <AiRecommendations recommendations={data.recommendations || []} />
              {data.segmentation && <section className="empty-panel"><h2>Segmentation</h2><pre>{JSON.stringify(data.segmentation, null, 2)}</pre></section>}
              {data.forecasting && <section className="empty-panel"><h2>Forecasting</h2><pre>{JSON.stringify(data.forecasting, null, 2)}</pre></section>}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
