import { useMemo, useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import ErrorMessage from '../components/common/ErrorMessage';
import Loader from '../components/common/Loader';
import { useAnalysis } from '../hooks/useAnalysis';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';
import { demoTrendData } from '../data/demoTrendData';
import uploadApi from '../api/uploadApi';
import { useEffect } from 'react';

function validTrend(rows) {
  if (!Array.isArray(rows)) return [];
  return rows.filter((row) => {
    const date = typeof row?.date === 'string' ? new Date(`${row.date}T00:00:00`) : new Date(row?.date);
    return row?.date && !Number.isNaN(date.getTime()) && Number.isFinite(Number(row.spend)) && Number.isFinite(Number(row.revenue));
  }).map((row) => ({ ...row, date: new Date(`${row.date}T00:00:00`).toISOString().slice(0, 10), spend: Number(row.spend), revenue: Number(row.revenue) })).sort((a, b) => a.date.localeCompare(b.date));
}
function TrendLine({ rows }) {
  const width = 760, height = 245, pad = 28;
  const max = Math.max(1, ...rows.flatMap((r) => [r.spend, r.revenue]));
  const points = (key) => rows.map((r, i) => `${pad + (i * (width - pad * 2)) / Math.max(1, rows.length - 1)},${height - pad - (r[key] / max) * (height - pad * 2)}`).join(' ');
  return <div className="trend-svg-wrap"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Spend and revenue performance trend"><g className="chart-grid-lines">{[0,1,2,3].map((n) => <line key={n} x1={pad} x2={width-pad} y1={pad+n*(height-pad*2)/3} y2={pad+n*(height-pad*2)/3} />)}</g><polyline className="trend-line spend-line" points={points('spend')} /><polyline className="trend-line revenue-line" points={points('revenue')} />{rows.map((r,i) => { const x=pad+i*(width-pad*2)/Math.max(1,rows.length-1); return <g key={`${r.date}-${i}`}><circle className="trend-point spend-point" cx={x} cy={height-pad-(r.spend/max)*(height-pad*2)} r="3"><title>{r.date}: spend {r.spend}</title></circle><circle className="trend-point revenue-point" cx={x} cy={height-pad-(r.revenue/max)*(height-pad*2)} r="3"><title>{r.date}: revenue {r.revenue}</title></circle></g>; })}</svg><div className="trend-date-labels">{rows.map((r) => <span key={r.date}>{new Date(`${r.date}T00:00:00`).toLocaleDateString(undefined,{month:'short',day:'numeric'})}</span>)}</div></div>;
}
function MetricBars({ title, note, rows, field, format = (v) => Number(v).toLocaleString(), empty, color = 'green' }) {
  const usable = (rows || []).filter((r) => Number.isFinite(Number(r[field])));
  const max = Math.max(1, ...usable.map((r) => Number(r[field])));
  return <section className="panel metric-chart"><div className="panel-heading"><div><p className="eyebrow">ANALYSIS</p><h2>{title}</h2><p className="panel-subtitle">{note}</p></div></div>{!usable.length ? <p className="panel-empty">{empty}</p> : <div className="metric-bars">{usable.slice(0,10).map((r,i) => <div className="metric-bar-row" key={`${r.label}-${i}`}><span title={r.label}>{r.label}</span><span className="metric-bar-track"><i className={color} style={{width:`${Math.max(Number(r[field]) > 0 ? 1 : 0, Number(r[field])/max*100)}%`}} /></span><b>{format(r[field])}</b></div>)}</div>}</section>;
}
function aggregateChannels(rows) { const map=new Map(); (rows||[]).forEach((r)=>{ const key=r.channel||'Unspecified'; const x=map.get(key)||{label:key,spend:0,revenue:0,revenueOK:true,conversions:0}; x.spend+=Number(r.spend)||0; x.conversions+=Number(r.conversions)||0; if(r.revenue==null || !Number.isFinite(Number(r.revenue))) x.revenueOK=false; else x.revenue+=Number(r.revenue); map.set(key,x); }); return [...map.values()].map(x=>({...x,revenue:x.revenueOK?x.revenue:null,roas:x.revenueOK&&x.spend?x.revenue/x.spend:null})); }

export default function Graphs({ user }) {
  const workspace=useDatasetWorkspace(); const [retry,setRetry]=useState(0); const {data,loading,error}=useAnalysis(workspace.datasetId,retry); const [campaigns,setCampaigns]=useState([]); const [campaignError,setCampaignError]=useState('');
  useEffect(()=>{ if(!workspace.datasetId){setCampaigns([]);return;} let active=true; setCampaignError(''); uploadApi.getDatasetCampaigns(workspace.datasetId).then((rows)=>{if(active)setCampaigns(Array.isArray(rows)?rows:[])}).catch((e)=>{if(active)setCampaignError(e.message)}); return ()=>{active=false}; },[workspace.datasetId,retry]);
  const realTrend=useMemo(()=>validTrend(data?.trends),[data]); const isReal=realTrend.length>0; const trend=isReal?realTrend:demoTrendData; const channels=useMemo(()=>aggregateChannels(campaigns),[campaigns]);
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}><div className="page-heading"><div><p className="eyebrow">ANALYTICS WORKSPACE</p><h1>Graphs &amp; Trends</h1><p>Explore campaign performance, marketing spend, revenue, and channel efficiency.</p></div><div className="heading-tools">{workspace.datasets.length>0&&<select aria-label="Selected dataset" value={workspace.datasetId} onChange={(e)=>workspace.selectDataset(e.target.value)}>{workspace.datasets.map(d=><option key={d.id} value={d.id}>{d.filename}</option>)}</select>}<button className="button button-secondary" onClick={()=>setRetry((n)=>n+1)} disabled={loading}>Refresh</button></div></div>
    {workspace.loading&&<Loader message="Loading datasets…"/>}{workspace.error&&<div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh}/></div>}{!workspace.datasetId&&!workspace.loading&&<div className="panel panel-empty">Upload a dataset to explore campaign and channel charts. The trend preview below is illustrative.</div>}
    <section className="panel trend-feature"><div className="panel-heading"><div><p className="eyebrow">OVER TIME · {isReal?'UPLOADED DATA':'ILLUSTRATION'}</p><h2>Spend &amp; revenue trend</h2><p className="panel-subtitle">{isReal?'Validated dated records from the selected dataset.':'Illustrative demo data — real dated records unavailable.'}</p></div><span className={`source-badge ${isReal?'source-real':'source-demo'}`}>{isReal?'Real dataset':'Demo data'}</span></div>{error&&<ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/>}<div className="trend-legend"><span><i className="legend-swatch spend-swatch"/> Spend</span><span><i className="legend-swatch revenue-swatch"/> Revenue</span></div><TrendLine rows={trend}/><p className="chart-footnote">{isReal?'Values use the dataset currency, which is not provided by the API.':'Illustration is stored locally and is never submitted as analytics.'}</p></section>
    {loading&&<div className="dashboard-loading"><Loader message="Loading analysis…"/></div>}{error&&<div className="dashboard-feedback"><ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/></div>}
    {data && (
      <>
        <PerformanceChart data={data.performance || []} />
        <div className="additional-chart-grid">
          <MetricBars title="Channel performance · ROAS" note="Revenue divided by spend when both values are available." rows={channels} field="roas" format={(value) => `${Number(value).toFixed(2)}×`} empty="Channel spend and revenue are unavailable for this dataset." color="gold" />
          <MetricBars title="Conversions by channel" note="Recorded conversion counts from uploaded campaign rows." rows={channels} field="conversions" format={(value) => Number(value).toLocaleString()} empty="The dataset contains no channel conversion counts." />
          <MetricBars title="Spend distribution by channel" note="Actual spend totals from campaign records." rows={channels} field="spend" format={(value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })} empty="No spend-by-channel records are available." color="gold" />
        </div>
        {campaignError && <p className="inline-note">Channel charts unavailable: {campaignError}</p>}
      </>
    )}
  </WorkspacePage>;
}
