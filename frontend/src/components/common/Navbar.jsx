import React from 'react';

export default function Navbar({ user }) {
  const displayName = user?.name || user?.full_name || user?.email || 'Account';
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('dataset_id');
    window.location.assign('/login');
  };
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <h2>Market Orbit</h2>
        <span>Marketing Intelligence</span>
      </div>

      <div className="navbar-user">
        <div className="user-avatar" aria-hidden="true">{displayName.charAt(0).toUpperCase()}</div>

        <div className="user-info">
          <strong>{displayName}</strong>
          <span>{user?.email || 'Marketing Analyst'}</span>
        </div>

        <button className="logout-button" onClick={logout} type="button">
          Logout
        </button>
      </div>
    </header>
  );
}
