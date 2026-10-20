import React from 'react';
import { logout } from '../../utils/session';

const items = [
  { href: '/dashboard', label: 'Dashboard', icon: '◫' },
  { href: '/upload', label: 'Upload Dataset', icon: '↑' },
  { href: '/graphs', label: 'Graphs & Trends', icon: '⌁' },
  { href: '/recommendations', label: 'AI Recommendations', icon: '✳' },
  { href: '/live-data', label: 'Live Data', icon: '◉' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
];

export default function Sidebar({ user: authenticatedUser }) {
  const path = window.location.pathname;
  const storedUser = (() => { try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; } })();
  const user = authenticatedUser || storedUser;
  const name = user?.name || user?.full_name || '';
  const email = user?.email || '';
  const initials = (name || email || 'MO').split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'MO';

  return (
    <aside className="sidebar">
      <a className="sidebar-brand" href="/dashboard" aria-label="Market Orbit dashboard">
        <span className="sidebar-brand-mark" aria-hidden="true">M</span>
        <span><strong>Market Orbit</strong><small>Marketing Intelligence</small></span>
      </a>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {items.map((item) => {
          const active = path === item.href;
          return <a key={item.href} aria-current={active ? 'page' : undefined} href={item.href} className={`sidebar-link ${active ? 'active' : ''}`}>
            <span className="sidebar-nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
          </a>;
        })}
      </nav>
      <div className="sidebar-account">
        <span className="sidebar-account-avatar" aria-hidden="true">{initials}</span>
        <span className="sidebar-account-copy"><strong>{name || 'Your account'}</strong><small>{email || 'Signed in'}</small></span>
      </div>
      <button type="button" className="sidebar-signout" onClick={logout}>Sign out</button>
    </aside>
  );
}
