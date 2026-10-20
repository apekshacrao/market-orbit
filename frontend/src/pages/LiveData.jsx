import { useEffect, useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import ErrorMessage from '../components/common/ErrorMessage';
import Loader from '../components/common/Loader';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';
import uploadApi from '../api/uploadApi';

export default function LiveData({ user }) {
  const workspace=useDatasetWorkspace(); const [rows,setRows]=useState([]); const [loading,setLoading]=useState(false); const [error,setError]=useState(''); const [fetchedAt,setFetchedAt]=useState(null); const [retry,setRetry]=useState(0);
  useEffect(()=>{ if(!workspace.datasetId){setRows([]);return;} let active=true;setLoading(true);setError(''); uploadApi.getDatasetCampaigns(workspace.datasetId).then(result=>{if(active){setRows(Array.isArray(result)?result:[]);setFetchedAt(new Date());}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false};},[workspace.datasetId,retry]);
  const money=(v)=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString(undefined,{maximumFractionDigits:2});
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}><div className="page-heading"><div><p className="eyebrow">DATA CONNECTION</p><h1>Live Data</h1><p>Inspect the latest records available from your uploaded dataset.</p></div><button className="button button-secondary" onClick={()=>setRetry(n=>n+1)} disabled={loading}>↻ Refresh data</button></div>
    {workspace.loading&&<Loader message="Finding the latest dataset…"/>}{workspace.error&&<div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh}/></div>}
    <section className="panel live-status-panel"><span className={`status-indicator ${workspace.selectedDataset?'available':'unavailable'}`}/><div><p className="eyebrow">SOURCE STATUS</p><h2>{workspace.selectedDataset?'Latest uploaded dataset':'No dataset selected'}</h2><p>{workspace.selectedDataset?`Snapshot from ${workspace.selectedDataset.filename}. This view is not a live stream.`:'Upload a dataset to see its records.'}</p></div><div className="live-meta"><span>Dataset status</span><strong>{workspace.selectedDataset?.status||'Unavailable'}</strong><span>Last fetched here</span><strong>{fetchedAt?fetchedAt.toLocaleString():'Not fetched yet'}</strong></div></section>
    <p className="source-note">The backend currently provides uploaded dataset records and processing status, but no streaming or periodic live-data endpoint. Refresh fetches the selected dataset again.</p>
    {error&&<div className="dashboard-feedback"><ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/></div>}{loading&&<Loader message="Fetching dataset records…"/>}
    {!loading&&workspace.datasetId&&<section className="panel live-records"><div className="panel-heading"><div><p className="eyebrow">CAMPAIGN RECORDS</p><h2>Latest available records</h2></div><span className="record-count">{rows.length} records</span></div>{!rows.length&&!error?<p className="panel-empty">No campaign rows are available for this dataset.</p>:<div className="table-scroll"><table><thead><tr><th>Campaign</th><th>Channel</th><th>Spend</th><th>Revenue</th><th>Conversions</th><th>Date</th></tr></thead><tbody>{rows.slice(-50).reverse().map((r,i)=><tr key={`${r.campaign_name||r.campaignName}-${i}`}><td>{r.campaign_name||r.campaignName||'—'}</td><td>{r.channel||'—'}</td><td>{money(r.spend)}</td><td>{money(r.revenue)}</td><td>{r.conversions==null?'—':Number(r.conversions).toLocaleString()}</td><td>{r.date||'—'}</td></tr>)}</tbody></table></div>}</section>}
  </WorkspacePage>;
}
