import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Graphs from './pages/Graphs';
import Recommendations from './pages/Recommendations';
import LiveData from './pages/LiveData';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import authApi from './api/authApi';
import Loader from './components/common/Loader';
import ErrorMessage from './components/common/ErrorMessage';

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null');
  } catch {
    return null;
  }
}

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [user, setUser] = useState(readStoredUser);
  const [checkingSession, setCheckingSession] = useState(Boolean(localStorage.getItem('token')));
  const [sessionError, setSessionError] = useState('');
  const [retry, setRetry] = useState(0);
  const token = localStorage.getItem('token');
  const protectedPath = ['/dashboard', '/upload', '/graphs', '/recommendations', '/live-data', '/settings'].includes(path);
  const authPage = ['/', '/login', '/register'].includes(path);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('reduce-motion', localStorage.getItem('market-orbit-reduced-motion') === 'true');
  }, []);

  useEffect(() => {
    if (checkingSession) return;
    if (protectedPath && (!token || !user)) window.location.replace('/login');
    if (authPage && token && user) window.location.replace('/dashboard');
  }, [authPage, checkingSession, protectedPath, token, user]);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setCheckingSession(false);
      setSessionError('');
      return undefined;
    }

    let active = true;
    setCheckingSession(true);
    setSessionError('');
    authApi.getCurrentUser()
      .then((currentUser) => {
        if (!active) return;
        setUser(currentUser);
        localStorage.setItem('user', JSON.stringify(currentUser));
      })
      .catch((error) => {
        if (!active) return;
        if (error.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
        } else {
          setSessionError(error.message);
        }
      })
      .finally(() => { if (active) setCheckingSession(false); });

    return () => { active = false; };
  }, [retry]);

  useEffect(() => {
    const onUnauthorized = () => {
      localStorage.removeItem('user');
      setUser(null);
      if (window.location.pathname !== '/login') window.location.assign('/login');
    };
    window.addEventListener('auth:unauthorized', onUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized);
  }, []);

  if (checkingSession) return <Loader message="Restoring your session…" />;
  if (token && sessionError) {
    return <main className="session-error"><ErrorMessage message={sessionError} onRetry={() => setRetry((value) => value + 1)} /><a href="/login">Return to sign in</a></main>;
  }

  if (protectedPath && (!token || !user)) {
    return <Loader message="Redirecting to sign in…" />;
  }
  if ((path === '/' || path === '/login' || path === '/register') && token && user) {
    return <Loader message="Opening your workspace…" />;
  }

  if (path === '/register') return <Register />;
  if (path === '/dashboard') return <Dashboard user={user} />;
  if (path === '/upload') return <Upload user={user} />;
  if (path === '/graphs') return <Graphs user={user} />;
  if (path === '/recommendations') return <Recommendations user={user} />;
  if (path === '/live-data') return <LiveData user={user} />;
  if (path === '/settings') return <Settings user={user} />;
  if (path === '/' || path === '/login') return <Login />;
  return <main className="session-error"><p className="eyebrow">404 · PAGE NOT FOUND</p><h1>This workspace page does not exist.</h1><a className="button button-primary" href={user ? '/dashboard' : '/login'}>{user ? 'Return to dashboard' : 'Go to sign in'}</a></main>;
}
