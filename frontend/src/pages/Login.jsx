import React from 'react';
import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const { login, loading, error } = useAuth();

 return (
  <div className="page-container auth-page">
    <div className="auth-brand">
      <h1>Market Orbit</h1>
      <p>AI-powered marketing performance insights.</p>
    </div>

    <div className="auth-form-container">
      <LoginForm onSubmit={login} loading={loading} error={error} />
    </div>
  </div>
);
}
