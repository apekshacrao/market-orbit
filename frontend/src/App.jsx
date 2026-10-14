import React from 'react';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';

export default function App() {
  const path = window.location.pathname;

  if (path === '/upload') {
    return <Upload />;
  }

  return <Dashboard />;
}