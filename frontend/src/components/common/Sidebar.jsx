import React from 'react';

const items = [
  { href: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { href: '/upload', label: 'Upload dataset', icon: 'upload' },
  { href: '/graphs', label: 'Graphs & trends', icon: 'chart' },
  { href: '/recommendations', label: 'AI recommendations', icon: 'spark' },
  { href: '/live-data', label: 'Dataset records', icon: 'table' },
  { href: '/settings', label: 'Settings', icon: 'settings' },
];

export function NavIcon({ name }) {
  const paths = {
    dashboard: <><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="5" rx="1.5"/><rect x="13" y="10" width="8" height="11" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/></>,
    upload: <><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5"/><path d="M5 14v5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5"/></>,
    chart: <><path d="M4 19V5m0 14h17"/><path d="m7 15 4-4 3 2 6-7"/></>,
    spark: <><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z"/><path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14Z"/></>,
    table: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11m6-11v11"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1a1.7 1.7 0 1 1-2.4 2.4l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a1.7 1.7 0 1 1-3.4 0v-.2a1.7 1.7 0 0 0-2.9-1.2l-.1.1a1.7 1.7 0 1 1-2.4-2.4l.1-.1a1.7 1.7 0 0 0-1.2-2.9H4a1.7 1.7 0 1 1 0-3.4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a1.7 1.7 0 1 1 2.4-2.4l.1.1a1.7 1.7 0 0 0 2.9-1.2V2a1.7 1.7 0 1 1 3.4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a1.7 1.7 0 1 1 2.4 2.4l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a1.7 1.7 0 1 1 0 3.4h-.2a1.7 1.7 0 0 0-1.2 2.9Z"/></>,
  };
  return <svg className="sidebar-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

export default function Sidebar() {
  const path = window.location.pathname;
  return (
    <aside className="sidebar">
      <p className="sidebar-section-label">WORKSPACE</p>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {items.map((item) => {
          const active = path === item.href;
          return <a key={item.href} aria-current={active ? 'page' : undefined} href={item.href} className={`sidebar-link ${active ? 'active' : ''}`}>
            <NavIcon name={item.icon}/><span>{item.label}</span>
          </a>;
        })}
      </nav>
    </aside>
  );
}
