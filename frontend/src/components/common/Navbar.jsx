import React from 'react';
import { logout } from '../../utils/session';

const pageLabels = {
  '/dashboard': 'Dashboard',
  '/upload': 'Upload dataset',
  '/graphs': 'Graphs & trends',
  '/recommendations': 'AI recommendations',
  '/live-data': 'Dataset records',
  '/settings': 'Settings',
};

export default function Navbar({ user, datasetName }) {
  const displayName = user?.name || user?.full_name || user?.email || 'Account';
  const pageLabel = pageLabels[window.location.pathname] || 'Workspace';
  return (
    <header className="navbar">
      <a className="navbar-brand" href="/dashboard" aria-label="Market Orbit dashboard">
        <span className="navbar-brand-mark" aria-hidden="true">M</span>
        <span><strong>Market Orbit</strong><small>Marketing Intelligence</small></span>
      </a>
      <div className="navbar-context" aria-label="Current workspace page and dataset">
        <span>{pageLabel}</span>
        {datasetName && <><i aria-hidden="true">/</i><strong title={datasetName}>{datasetName}</strong></>}
      </div>
      <div className="navbar-user">
        <div className="user-avatar" aria-hidden="true">{displayName.charAt(0).toUpperCase()}</div>
        <div className="user-info"><strong>{displayName}</strong><span>{user?.email || 'Marketing Analyst'}</span></div>
        <button className="logout-button" onClick={logout} type="button">Sign out</button>
      </div>
    </header>
  );
}
