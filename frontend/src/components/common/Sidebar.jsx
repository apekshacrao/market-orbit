import React from 'react';

export default function Sidebar() {
  const path = window.location.pathname;

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <a
          aria-current={path === '/dashboard' ? 'page' : undefined}
          href="/dashboard"
          className={`sidebar-link ${path === '/dashboard' ? 'active' : ''}`}
        >
          Dashboard
        </a>

        <a
          aria-current={path === '/upload' ? 'page' : undefined}
          href="/upload"
          className={`sidebar-link ${path === '/upload' ? 'active' : ''}`}
        >
          Upload Data
        </a>
      </nav>
    </aside>
  );
}
