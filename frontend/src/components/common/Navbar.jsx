import React from 'react';

export default function Navbar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <h1>AI Marketing Analyzer</h1>
      </div>
      <div className="nav-links">
        {user ? (
          <>
            <span className="user-email">{user.email}</span>
            <button onClick={onLogout} className="logout-button">Logout</button>
          </>
        ) : (
          <span>Welcome</span>
        )}
      </div>
    </nav>
  );
}
