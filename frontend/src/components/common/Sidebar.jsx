import React from 'react';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <a href="/dashboard" className="sidebar-link active">
          Dashboard
        </a>

        <a href="/upload" className="sidebar-link">
          Upload Data
        </a>

        <a href="/analytics" className="sidebar-link">
          Analytics
        </a>
      </nav>
    </aside>
  );
}