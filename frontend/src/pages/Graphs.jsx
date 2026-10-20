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
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function validTrend(rows) {
  if (!Array.isArray(rows)) return [];
  return rows.filter((row) => {
    if (typeof row?.date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.date)) return false;
    const date = new Date(`${row.date}T00:00:00`);
    return date.toISOString().slice(0, 10) === row.date
      && row.spend != null && Number.isFinite(Number(row.spend))
      && row.revenue != null && Number.isFinite(Number(row.revenue));
  }).map((row) => ({ ...row, date: new Date(`${row.date}T00:00:00`).toISOString().slice(0, 10), spend: Number(row.spend), revenue: Number(row.revenue) })).sort((a, b) => a.date.localeCompare(b.date));
}
function TrendLine({ rows }) {
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('reduce-motion');
  const hasConversions = rows.some((row) => row.conversions != null && Number.isFinite(Number(row.conversions)));
  const compact = (value) => new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(value);
  return <div className="trend-chart-area"><ResponsiveContainer width="100%" height={310}>
    <LineChart data={rows} margin={{ top: 8, right: hasConversions ? 12 : 20, bottom: 4, left: 8 }}>
      <CartesianGrid stroke="#353C30" strokeDasharray="3 4" vertical={false}/>
      <XAxis dataKey="date" stroke="#AAA99A" tick={{ fontSize: 11 }} tickFormatter={(value) => new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}/>
      <YAxis yAxisId="metrics" stroke="#AAA99A" tick={{ fontSize: 11 }} tickFormatter={compact} width={48}/>
      {hasConversions && <YAxis yAxisId="conversions" orientation="right" stroke="#AAA99A" tick={{ fontSize: 11 }} width={42}/>}
      <Tooltip contentStyle={{ backgroundColor: '#171B15', border: '1px solid #353C30', borderRadius: '8px', color: '#E7E3D6' }} labelFormatter={(value) => new Date(`${value}T00:00:00`).toLocaleDateString()} formatter={(value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}/>
      <Legend/>
      <Line yAxisId="metrics" type="monotone" dataKey="spend" name="Spend" stroke="#78966A" strokeWidth={3} dot={false} isAnimationActive={!reducedMotion} animationDuration={650}/>
      <Line yAxisId="metrics" type="monotone" dataKey="revenue" name="Revenue" stroke="#C5A15B" strokeWidth={3} dot={false} isAnimationActive={!reducedMotion} animationDuration={650}/>
      {hasConversions && <Line yAxisId="conversions" type="monotone" dataKey="conversions" name="Conversions" stroke="#8BB58A" strokeWidth={2} dot={false} isAnimationActive={!reducedMotion} animationDuration={650}/>}
    </LineChart>
  </ResponsiveContainer></div>;
}
function MetricBars({ title, note, rows, field, format = (v) => Number(v).toLocaleString(), empty, color = 'green' }) {
  const usable = (rows || []).filter((r) => r[field] != null && Number.isFinite(Number(r[field])));
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
          <MetricBars title="ROAS by campaign" note="Campaign return on ad spend reported by the analysis." rows={(data.performance || []).map((item) => ({ ...item, label: item.campaignName || 'Unnamed campaign' }))} field="roas" format={(value) => `${Number(value).toFixed(2)}×`} empty="Campaign ROAS is unavailable for this dataset." color="gold" />
          <MetricBars title="Channel performance · ROAS" note="Revenue divided by spend when both values are available." rows={channels} field="roas" format={(value) => `${Number(value).toFixed(2)}×`} empty="Channel spend and revenue are unavailable for this dataset." color="gold" />
          <MetricBars title="Conversions by channel" note="Recorded conversion counts from uploaded campaign rows." rows={channels} field="conversions" format={(value) => Number(value).toLocaleString()} empty="The dataset contains no channel conversion counts." />
          <MetricBars title="Spend distribution by channel" note="Actual spend totals from campaign records." rows={channels} field="spend" format={(value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })} empty="No spend-by-channel records are available." color="gold" />
        </div>
        {campaignError && <p className="inline-note">Channel charts unavailable: {campaignError}</p>}
        {data.segmentation && <section className="panel supplemental-analysis"><h2>Segmentation</h2><pre>{JSON.stringify(data.segmentation, null, 2)}</pre></section>}
        {data.forecasting && <section className="panel supplemental-analysis"><h2>Forecasting</h2><pre>{JSON.stringify(data.forecasting, null, 2)}</pre></section>}
      </>
    )}
  </WorkspacePage>;
}
