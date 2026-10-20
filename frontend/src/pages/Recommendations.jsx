import { useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import AiRecommendations from '../components/dashboard/AiRecommendations';
import ErrorMessage from '../components/common/ErrorMessage';
import Loader from '../components/common/Loader';
import { useAnalysis } from '../hooks/useAnalysis';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';

export default function Recommendations({ user }) {
  const workspace=useDatasetWorkspace(); const [retry,setRetry]=useState(0); const {data,loading,error}=useAnalysis(workspace.datasetId,retry);
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}><div className="page-heading"><div><p className="eyebrow">DECISION SUPPORT</p><h1>AI Recommendations</h1><p>Review actions produced by the analysis for your selected dataset.</p></div><div className="heading-tools">{workspace.datasets.length>0&&<select aria-label="Selected dataset" value={workspace.datasetId} onChange={e=>workspace.selectDataset(e.target.value)}>{workspace.datasets.map(d=><option key={d.id} value={d.id}>{d.filename}</option>)}</select>}<button className="button button-secondary" onClick={()=>setRetry(n=>n+1)} disabled={loading}>Refresh results</button></div></div>
    {workspace.loading&&<Loader message="Loading datasets…"/>}{workspace.error&&<div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh}/></div>}{!workspace.datasetId&&!workspace.loading&&<section className="panel panel-empty">Upload a dataset to view recommendations from its analysis.</section>}{loading&&<Loader message="Fetching recommendations…"/>}{error&&<div className="dashboard-feedback"><ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/></div>}{data&&<><p className="source-note">Recommendations are returned by the backend analysis for <strong>{workspace.selectedDataset?.filename}</strong>. Refresh reloads those results; this backend does not expose a separate regeneration action.</p><AiRecommendations recommendations={data.recommendations||[]}/></>}
  </WorkspacePage>;
}
