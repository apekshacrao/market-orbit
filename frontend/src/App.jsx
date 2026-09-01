import React from 'react';
import Navbar from './components/common/Navbar';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <div className="app-layout">
      <Navbar />
      <main className="app-content">
        <Dashboard />
      </main>
    </div>
  );
}
