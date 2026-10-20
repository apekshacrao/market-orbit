import { useState } from 'react';

const items = [
  { href: '/dashboard', label: 'Dashboard', icon: '◫' },
  { href: '/upload', label: 'Upload Dataset', icon: '↑' },
  { href: '/graphs', label: 'Graphs & Trends', icon: '⌁' },
  { href: '/recommendations', label: 'AI Recommendations', icon: '✳' },
  { href: '/live-data', label: 'Live Data', icon: '◉' },
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const currentPath = window.location.pathname;
  return <>
    <button className="sidebar-mobile-toggle" type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>{open ? 'Close navigation' : '☰ Navigation'}</button>
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <a className="sidebar-brand" href="/dashboard"><span className="brand-mark">M</span><span>MARKET <b>ORBIT</b></span></a>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {items.map((item) => { const active = currentPath === item.href; return <a key={item.href} href={item.href} className={`sidebar-link ${active ? 'active' : ''}`} aria-current={active ? 'page' : undefined} onClick={() => setOpen(false)}><span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>{active && <span className="nav-indicator" aria-hidden="true" />}</a>; })}
      </nav>
      <a className={`sidebar-profile-link ${currentPath === '/settings' ? 'active' : ''}`} href="/settings" aria-current={currentPath === '/settings' ? 'page' : undefined} onClick={() => setOpen(false)}><span aria-hidden="true">⚙</span> Settings</a>
      <div className="sidebar-footer">MARKET ORBIT <span>v1.0</span></div>
    </aside>
    {open && <button className="sidebar-scrim" aria-label="Close navigation" type="button" onClick={() => setOpen(false)} />}
  </>;
}
