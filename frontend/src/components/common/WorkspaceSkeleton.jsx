import React from 'react';

function SkeletonLine({ className = '' }) {
  return <span className={`skeleton-line workspace-skeleton-line ${className}`} aria-hidden="true"/>;
}

function PanelSkeleton({ className = '', lines = 3 }) {
  return <div className={`workspace-skeleton-panel ${className}`} aria-hidden="true">
    <SkeletonLine className="panel-title"/>
    <SkeletonLine className="panel-copy"/>
    <div className="panel-placeholder-lines">{Array.from({ length: lines }, (_, index) => <SkeletonLine key={index}/>)}</div>
  </div>;
}

export default function WorkspaceSkeleton({ message = 'Restoring your workspace…' }) {
  const route = window.location.pathname.split('/')[1] || 'dashboard';
  const isDashboard = route === 'dashboard';
  const isGraphs = route === 'graphs';
  const isUpload = route === 'upload';
  const isSettings = route === 'settings';
  const isRecords = route === 'live-data';
  const isRecommendations = route === 'recommendations';

  return <div className="workspace-skeleton" role="status" aria-label={message} aria-busy="true">
    <span className="visually-hidden">{message}</span>
    <header className="workspace-skeleton-navbar" aria-hidden="true">
      <span className="skeleton-line workspace-skeleton-mark"/>
      <span className="workspace-skeleton-brand"><SkeletonLine/><SkeletonLine/></span>
      <SkeletonLine className="workspace-skeleton-context"/>
      <SkeletonLine className="workspace-skeleton-user"/>
    </header>
    <div className="workspace-skeleton-layout" aria-hidden="true">
      <aside className="workspace-skeleton-sidebar">
        <SkeletonLine className="workspace-skeleton-nav-label"/>
        {Array.from({ length: 6 }, (_, index) => <SkeletonLine key={index} className="workspace-skeleton-nav-item"/>)}
      </aside>
      <main className="workspace-skeleton-main">
        <div className="workspace-skeleton-heading"><div><SkeletonLine className="workspace-skeleton-eyebrow"/><SkeletonLine className="workspace-skeleton-title"/><SkeletonLine className="workspace-skeleton-subtitle"/></div><div className="workspace-skeleton-actions"><SkeletonLine/><SkeletonLine/></div></div>
        {isDashboard && <><div className="workspace-skeleton-kpis">{Array.from({ length: 5 }, (_, index) => <PanelSkeleton key={index} className="workspace-skeleton-kpi" lines={1}/>)}</div><PanelSkeleton className="workspace-skeleton-primary-panel" lines={5}/><div className="workspace-skeleton-columns"><PanelSkeleton/><PanelSkeleton/></div></>}
        {isGraphs && <><PanelSkeleton className="workspace-skeleton-primary-panel" lines={5}/><div className="workspace-skeleton-columns"><PanelSkeleton/><PanelSkeleton/></div></>}
        {isUpload && <PanelSkeleton className="workspace-skeleton-upload" lines={4}/>}
        {isRecommendations && <PanelSkeleton className="workspace-skeleton-primary-panel" lines={6}/>}
        {isRecords && <PanelSkeleton className="workspace-skeleton-primary-panel" lines={8}/>}
        {isSettings && <div className="workspace-skeleton-columns"><PanelSkeleton lines={4}/><PanelSkeleton lines={4}/></div>}
        {!isDashboard&&!isGraphs&&!isUpload&&!isSettings&&!isRecords&&!isRecommendations&&<PanelSkeleton className="workspace-skeleton-primary-panel" lines={5}/>}
      </main>
    </div>
  </div>;
}
