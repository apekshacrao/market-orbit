import { useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import AiRecommendations from '../components/dashboard/AiRecommendations';
import ErrorMessage from '../components/common/ErrorMessage';
import Loader from '../components/common/Loader';
import DatasetSelector from '../components/common/DatasetSelector';
import { useAnalysis } from '../hooks/useAnalysis';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';

export default function Recommendations({ user }) {
  const workspace=useDatasetWorkspace(); const [retry,setRetry]=useState(0); const {data,loading,error}=useAnalysis(workspace.datasetId,retry);
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}><div className="page-heading"><div><p className="eyebrow">DECISION SUPPORT</p><h1>AI Recommendations</h1><p>Review suggested actions based on your campaign performance.</p></div><div className="heading-tools"><DatasetSelector datasets={workspace.datasets} datasetId={workspace.datasetId} onChange={workspace.selectDataset}/><button className="button button-secondary" onClick={()=>setRetry(n=>n+1)} disabled={loading||!workspace.datasetId}>{loading?'Refreshing…':'Refresh analysis'}</button></div></div>
    {workspace.loading&&<Loader message="Loading datasets…"/>}{workspace.error&&<div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh}/></div>}{!workspace.datasetId&&!workspace.loading&&<section className="panel panel-empty">Upload a dataset to view recommendations based on its analysis. <a href="/upload">Upload a dataset</a></section>}{loading&&<Loader message="Loading recommendations…"/>}{error&&<div className="dashboard-feedback"><ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/></div>}{data&&<><p className="source-note">Recommendations are based on <strong>{workspace.selectedDataset?.filename}</strong>. Refresh loads the latest available analysis.</p><AiRecommendations recommendations={data.recommendations||[]}/></>}
  </WorkspacePage>;
}
