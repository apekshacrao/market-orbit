import { useState } from 'react';

export default function Navbar({ user, datasetName, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const label = user?.name || user?.email || 'Your workspace';
  const initials = label.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'MO';

  return (
    <header className="topbar">
      <a className="brand-lockup topbar-brand" href="/dashboard" aria-label="Market Orbit dashboard"><span className="brand-mark" aria-hidden="true">M</span><span>MARKET <b>ORBIT</b></span></a>
      <div className="topbar-context"><span className="context-kicker">WORKSPACE</span><span>{datasetName || 'Marketing intelligence'}</span></div>
      <div className="topbar-actions">
        <div className="user-menu-wrap">
          <button className="user-menu-trigger" type="button" onClick={() => setMenuOpen((open) => !open)} aria-expanded={menuOpen} aria-label={`Account menu for ${label}`}>
            <span className="user-avatar" aria-hidden="true">{initials}</span><span className="user-name">{label}</span><span className="chevron" aria-hidden="true">⌄</span>
          </button>
          {menuOpen && <div className="user-menu"><span className="menu-user-label">Signed in as</span><strong>{user?.email || label}</strong><button type="button" onClick={onLogout}>Sign out</button></div>}
        </div>
      </div>
    </header>
  );
}
