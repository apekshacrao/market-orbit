import React from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';

export default function Dashboard() {
  return (
    <div className="dashboard-page">
      <Navbar />

      <div className="dashboard-layout">
        <Sidebar />

        <main className="dashboard-content">
          <h1>Dashboard</h1>
          <p>Welcome to your marketing performance dashboard.</p>
        </main>
      </div>
    </div>
  );
}