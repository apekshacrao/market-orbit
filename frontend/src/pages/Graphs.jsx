import { useMemo, useState } from 'react';
import WorkspacePage from '../components/common/WorkspacePage';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import ErrorMessage from '../components/common/ErrorMessage';
import Loader from '../components/common/Loader';
import DatasetSelector from '../components/common/DatasetSelector';
import { useAnalysis } from '../hooks/useAnalysis';
import { useDatasetWorkspace } from '../hooks/useDatasetWorkspace';
import { demoTrendData } from '../data/demoTrendData';
import uploadApi from '../api/uploadApi';
import { useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import chartTheme, { chartTooltipStyle } from '../components/dashboard/chartTheme';

function validTrend(rows) {
  if (!Array.isArray(rows)) return [];
  return rows.filter((row) => {
    if (typeof row?.date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.date)) return false;
    const [year, month, day] = row.date.split('-').map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.getUTCFullYear() === year
      && date.getUTCMonth() === month - 1
      && date.getUTCDate() === day
      && row.spend != null && Number.isFinite(Number(row.spend))
      && row.revenue != null && Number.isFinite(Number(row.revenue));
  }).map((row) => ({ ...row, spend: Number(row.spend), revenue: Number(row.revenue) })).sort((a, b) => a.date.localeCompare(b.date));
}
function TrendLine({ rows }) {
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('reduce-motion');
  const compact = (value) => new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
  const charts = [
    { key: 'spend', title: 'Spend', color: chartTheme.series.spend },
    { key: 'revenue', title: 'Revenue', color: chartTheme.series.revenue },
    { key: 'conversions', title: 'Conversions', color: chartTheme.series.conversions, optional: true },
  ].filter((chart) => !chart.optional || rows.some((row) => row[chart.key] != null && Number.isFinite(Number(row[chart.key]))));
  return <div className="trend-small-multiples" role="group" aria-label="Daily spend, revenue, and conversions trends" aria-describedby="trend-chart-summary">
    {charts.map(({ key, title, color }) => <section className="trend-metric-chart" key={key} aria-label={`${title} over time`}>
      <h3>{title}</h3>
      <div className="trend-chart-area"><ResponsiveContainer width="100%" height={190}>
        <LineChart data={rows} margin={{ top: 8, right: 18, bottom: 2, left: 8 }}>
          <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 4" vertical={false}/>
          <XAxis dataKey="date" stroke={chartTheme.muted} tick={{ fontSize: 10, fill: chartTheme.muted }} tickFormatter={(value) => new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}/>
          <YAxis stroke={chartTheme.muted} tick={{ fontSize: 10, fill: chartTheme.muted }} tickFormatter={compact} width={48}/>
          <Tooltip contentStyle={chartTooltipStyle} labelFormatter={(value) => new Date(`${value}T12:00:00`).toLocaleDateString('en-IN')} formatter={(value) => [Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 }), title]}/>
          <Line type="linear" dataKey={key} name={title} stroke={color} strokeWidth={2.5} dot={{ r: 3, fill: color, strokeWidth: 1 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={!reducedMotion} animationDuration={500}/>
        </LineChart>
      </ResponsiveContainer></div>
    </section>)}
    <details className="chart-data-details"><summary>View exact daily values</summary><div className="forecast-table-wrap"><table className="forecast-table"><caption className="visually-hidden">Daily spend, revenue, and conversions in the selected dataset</caption><thead><tr><th>Date</th><th>Spend</th><th>Revenue</th><th>Conversions</th></tr></thead><tbody>{rows.map((row) => <tr key={row.date}><td>{row.date}</td><td>{numberFormat(row.spend)}</td><td>{numberFormat(row.revenue)}</td><td>{numberFormat(row.conversions)}</td></tr>)}</tbody></table></div></details>
  </div>;
}
function MetricBars({ title, note, rows, field, format = (v) => Number(v).toLocaleString('en-IN'), empty, color = 'green' }) {
  const usable = (rows || []).filter((r) => r[field] != null && Number.isFinite(Number(r[field])));
  const max = Math.max(1, ...usable.map((r) => Number(r[field])));
  return <section className="panel metric-chart"><div className="panel-heading"><div><p className="eyebrow">ANALYSIS</p><h2>{title}</h2><p className="panel-subtitle">{note}</p></div></div>{!usable.length ? <p className="panel-empty">{empty}</p> : <div className="metric-bars">{usable.slice(0,10).map((r,i) => <div className="metric-bar-row" key={`${r.label}-${i}`}><span title={r.label}>{r.label}</span><span className="metric-bar-track"><i className={color} style={{width:`${Math.max(Number(r[field]) > 0 ? 1 : 0, Number(r[field])/max*100)}%`}} /></span><b>{format(r[field])}</b></div>)}</div>}</section>;
}
const cohortLabels = {
  scale_ready: 'Scale ready',
  volume_driver: 'Volume drivers',
  efficiency_niche: 'Efficiency niches',
  budget_drain: 'Budget watch',
};
const numberFormat = (value) => value == null || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 });
function SegmentationSummary({ segmentation }) {
  const cohortResult = segmentation?.cohorts || {};
  const summary = cohortResult.summary || {};
  const groups = cohortResult.cohorts || {};
  const portfolio = segmentation?.segment_portfolio;
  const hasGroups = Object.values(groups).some((items) => Array.isArray(items) && items.length);
  return <section className="panel supplemental-analysis">
    <div className="panel-heading"><div><p className="eyebrow">CAMPAIGN GROUPS</p><h2>Segmentation</h2><p className="panel-subtitle">Campaigns grouped by conversion volume and cost efficiency.</p></div><span className="record-count">{numberFormat(summary.total_campaigns)} campaigns</span></div>
    <div className="segmentation-summary">
      {Object.entries(cohortLabels).map(([key, label]) => <div className="segmentation-count" key={key}><span>{label}</span><strong>{numberFormat(summary[`${key}_count`] ?? groups[key]?.length ?? 0)}</strong></div>)}
    </div>
    {hasGroups ? <div className="cohort-grid">{Object.entries(cohortLabels).map(([key, label]) => {
      const items = groups[key] || [];
      return <article className="cohort-card" key={key}><h3>{label}<span>{items.length}</span></h3>{items.length ? <><ul>{items.slice(0, 4).map((item) => <li key={item.campaign_name}><strong>{item.campaign_name}</strong><span>{numberFormat(item.conversions)} conversions · CPA {numberFormat(item.cpa)} · ROAS {numberFormat(item.roas)}×</span></li>)}</ul>{items.length > 4 && <p className="cohort-more">+{items.length - 4} more campaigns</p>}</> : <p>No campaigns in this group.</p>}</article>;
    })}</div> : <p className="panel-empty">No campaign groups are available for this dataset.</p>}
    {portfolio && <div className="portfolio-note"><strong>Customer segment profile</strong><span>{portfolio.is_available ? `${numberFormat(portfolio.total_segments)} customer segments found.` : 'No customer segment column was provided in this upload.'}</span></div>}
  </section>;
}
function ForecastSummary({ forecasting }) {
  const coverage = forecasting?.historical_coverage || {};
  const forecast = forecasting?.forecasts || {};
  const models = forecast.models || {};
  const naive = models.naive;
  const points = Array.isArray(naive?.forecast) ? naive.forecast : [];
  const warnings = Array.isArray(forecasting?.warnings) ? forecasting.warnings : [];
  const status = forecasting?.status || 'unavailable';
  const statusLabels = { ready: 'Validated forecast', ready_basic: 'Basic forecast', ready_forecast_only: 'Forecast ready', ready_basic_forecast_only: 'Basic forecast', insufficient_history: 'More history needed', no_valid_dates: 'No dated records', unavailable: 'Unavailable' };
  const statusLabel = statusLabels[status] || status.replaceAll('_', ' ');
  const count = coverage.historical_dates_count ?? naive?.metadata?.historical_dates_count;
  return <section className="panel supplemental-analysis">
    <div className="panel-heading"><div><p className="eyebrow">OUTLOOK</p><h2>Forecasting</h2><p className="panel-subtitle">A simple baseline based on the latest observed values.</p></div><span className={`forecast-status ${status.includes('ready') ? 'available' : ''}`}>{statusLabel}</span></div>
    <div className="forecast-meta"><span><strong>{numberFormat(count)}</strong> historical dates</span>{coverage.start_date && coverage.end_date && <span>{coverage.start_date} – {coverage.end_date}</span>}{forecast.horizon && <span>{forecast.horizon}-day outlook</span>}</div>
    {warnings.length > 0 && <div className="forecast-notice"><strong>Forecast limits</strong><ul>{warnings.slice(0, 3).map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul></div>}
    {points.length > 0 && <div className="forecast-table-wrap"><table className="forecast-table"><thead><tr><th>Forecast date</th><th>Spend</th><th>Revenue</th><th>Conversions</th></tr></thead><tbody>{points.slice(0, 7).map((point) => <tr key={point.date}><td>{point.date}</td><td>{numberFormat(point.spend)}</td><td>{numberFormat(point.revenue)}</td><td>{numberFormat(point.conversions)}</td></tr>)}</tbody></table></div>}
    {points.length === 0 && warnings.length === 0 && <p className="panel-empty">A forecast is not available for this dataset yet.</p>}
    <p className="chart-footnote">Baseline estimates are directional and should not be treated as guaranteed results.</p>
  </section>;
}
function aggregateChannels(rows) { const map=new Map(); (rows||[]).forEach((r)=>{ const key=r.channel||'Unspecified'; const x=map.get(key)||{label:key,spend:0,revenue:0,revenueOK:true,conversions:0}; x.spend+=Number(r.spend)||0; x.conversions+=Number(r.conversions)||0; if(r.revenue==null || !Number.isFinite(Number(r.revenue))) x.revenueOK=false; else x.revenue+=Number(r.revenue); map.set(key,x); }); return [...map.values()].map(x=>({...x,revenue:x.revenueOK?x.revenue:null,roas:x.revenueOK&&x.spend?x.revenue/x.spend:null})); }

export default function Graphs({ user }) {
  const workspace=useDatasetWorkspace(); const [retry,setRetry]=useState(0); const {data,loading,error}=useAnalysis(workspace.datasetId,retry); const [campaigns,setCampaigns]=useState([]); const [campaignError,setCampaignError]=useState('');
  useEffect(()=>{ if(!workspace.datasetId){setCampaigns([]);return;} let active=true; setCampaignError(''); uploadApi.getDatasetCampaigns(workspace.datasetId).then((rows)=>{if(active)setCampaigns(Array.isArray(rows)?rows:[])}).catch((e)=>{if(active)setCampaignError(e.message)}); return ()=>{active=false}; },[workspace.datasetId,retry]);
  const realTrend=useMemo(()=>validTrend(data?.trends),[data]); const isReal=realTrend.length>0; const showDemo=Boolean(workspace.datasetId)&&!loading&&!error&&!isReal; const trend=isReal?realTrend:demoTrendData; const channels=useMemo(()=>aggregateChannels(campaigns),[campaigns]);
  const trendRange = isReal ? `${realTrend.length} dated records · ${realTrend[0].date}–${realTrend[realTrend.length-1].date}` : '';
  return <WorkspacePage user={user} datasetName={workspace.selectedDataset?.filename}><div className="page-heading"><div><p className="eyebrow">ANALYTICS WORKSPACE</p><h1>Graphs &amp; Trends</h1><p>Explore campaign performance, marketing spend, revenue, and channel efficiency.</p></div><div className="heading-tools"><DatasetSelector datasets={workspace.datasets} datasetId={workspace.datasetId} onChange={workspace.selectDataset}/><button className="button button-secondary" onClick={()=>setRetry((n)=>n+1)} disabled={loading||!workspace.datasetId}>{loading?'Refreshing…':'Refresh analysis'}</button></div></div>
    {workspace.loading&&<Loader message="Loading datasets…"/>}{workspace.error&&<div className="dashboard-feedback"><ErrorMessage message={workspace.error} onRetry={workspace.refresh}/></div>}
    <section className="panel trend-feature"><div className="panel-heading"><div><p className="eyebrow">OVER TIME · {isReal?'UPLOADED DATA':showDemo?'ILLUSTRATION':'DATA STATUS'}</p><h2>Spend, revenue &amp; conversions</h2><p className="panel-subtitle">{isReal?'Validated dated records from the selected dataset.':showDemo?'Illustrative demo data — real dated records unavailable.':'Select a dataset to explore its dated trend records.'}</p>{isReal&&<p className="panel-subtitle trend-range">{trendRange}</p>}</div><span className={`source-badge ${isReal?'source-real':showDemo?'source-demo':''}`}>{isReal?'Real dataset':showDemo?'Demo data':loading?'Loading':'No dataset'}</span></div>{error&&<ErrorMessage message={error} onRetry={()=>setRetry(n=>n+1)}/>}<p className="chart-summary" id="trend-chart-summary">{isReal?'Each metric uses its own scale. Points show daily totals from the uploaded data. Amounts use dataset units; currency is not provided.':showDemo?'Illustrative values are shown only as a preview and do not come from the uploaded dataset.': 'Add date, spend, and revenue columns to your CSV to explore trends.'}</p>{isReal||showDemo?<TrendLine rows={trend}/>:<div className="trend-empty-state">{loading?<Loader message="Loading trend data…"/>:error?<p>Trend data could not be loaded. Retry to fetch it again.</p>:<><p>{workspace.datasetId?'No trend records are available for this dataset.':'Upload a CSV with date and revenue columns to view trends.'}</p>{!workspace.datasetId&&<a className="primary-link-button" href="/upload">Upload a dataset</a>}</>}</div>}<p className="chart-footnote">{isReal?'Values use the dataset currency, which is not provided by the API.':showDemo?'Illustration is stored locally and is never submitted as analytics.':'Trend charts appear when dated dataset records are available.'}</p></section>
    {data && (
      <>
        <PerformanceChart data={data.performance || []} />
        <div className="additional-chart-grid">
          <MetricBars title="ROAS by campaign" note="Campaign return on ad spend reported by the analysis." rows={(data.performance || []).map((item) => ({ ...item, label: item.campaignName || 'Unnamed campaign' }))} field="roas" format={(value) => `${Number(value).toFixed(2)}×`} empty="Campaign ROAS is unavailable for this dataset." color="accent" />
          <MetricBars title="Channel performance · ROAS" note="Revenue divided by spend when both values are available." rows={channels} field="roas" format={(value) => `${Number(value).toFixed(2)}×`} empty="Channel spend and revenue are unavailable for this dataset." color="accent" />
          <MetricBars title="Conversions by channel" note="Recorded conversion counts from uploaded campaign rows." rows={channels} field="conversions" format={(value) => Number(value).toLocaleString('en-IN')} empty="The dataset contains no channel conversion counts." />
          <MetricBars title="Spend distribution by channel" note="Actual spend totals from campaign records." rows={channels} field="spend" format={(value) => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} empty="No spend-by-channel records are available." color="accent" />
        </div>
        {campaignError && <p className="inline-note">Channel charts unavailable: {campaignError}</p>}
        {data.segmentation && <SegmentationSummary segmentation={data.segmentation} />}
        {data.forecasting && <ForecastSummary forecasting={data.forecasting} />}
      </>
    )}
  </WorkspacePage>;
}
