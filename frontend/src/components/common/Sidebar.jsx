import React from 'react';

export default function Sidebar() {
  const path = window.location.pathname;

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <a
          href="/dashboard"
          className={`sidebar-link ${path === '/dashboard' ? 'active' : ''}`}
        >
          Dashboard
        </a>

        <a
          href="/upload"
          className={`sidebar-link ${path === '/upload' ? 'active' : ''}`}
        >
          Upload Data
        </a>
      </nav>
    </aside>
  );
}