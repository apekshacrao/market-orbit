import React from 'react';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <h2>Market Orbit</h2>
        <span>Marketing Intelligence</span>
      </div>

      <div className="navbar-user">
        <div className="user-avatar">U</div>

        <div className="user-info">
          <strong>User</strong>
          <span>Marketing Analyst</span>
        </div>

        <button className="logout-button">
          Logout
        </button>
      </div>
    </header>
  );
}