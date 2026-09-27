import React from 'react';
import Login from './pages/Login';
import Register from './pages/Register';

export default function App() {
  const path = window.location.pathname;

  if (path === '/register') {
    return <Register />;
  }

  return <Login />;
}