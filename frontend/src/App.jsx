import React, { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Login from './pages/Login';
import Register from './pages/Register';
import authApi from './api/authApi';
import Loader from './components/common/Loader';

function savedUser() {
  try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; }
}

export default function App() {
  const path = window.location.pathname;
  const [user, setUser] = useState(() => savedUser());
  const [checkingSession, setCheckingSession] = useState(Boolean(localStorage.getItem('token')));

  useEffect(() => {
    if (!localStorage.getItem('token')) return;
    let active = true;
    authApi.getCurrentUser()
      .then((currentUser) => { if (active) setUser(currentUser); })
      .catch(() => {
        if (!localStorage.getItem('token')) {
          localStorage.removeItem('user');
          if (active) setUser(null);
        }
      })
      .finally(() => { if (active) setCheckingSession(false); });
    return () => { active = false; };
  }, []);

  if (checkingSession) return <Loader message="Restoring your session…" />;

  const hasSession = Boolean(localStorage.getItem('token') && user);
  const protectedPath = ['/dashboard', '/upload'].includes(path);
  if (protectedPath && !hasSession) {
    window.location.replace('/login');
    return <Loader message="Redirecting to sign in…" />;
  }

  if ((path === '/' || path === '/login') && hasSession) {
    window.location.replace('/dashboard');
    return <Loader message="Opening your dashboard…" />;
  }

  if (path === '/register') return <Register />;
  if (path === '/dashboard') return <Dashboard user={user} />;
  if (path === '/upload') return <Upload user={user} />;
  if (path === '/' || path === '/login') return <Login />;
  return <Login />;
}
