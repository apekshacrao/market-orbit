import React from 'react';
import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const { login, loading, error } = useAuth();

  return (
    <div className="page-container auth-page">
      <LoginForm onSubmit={login} loading={loading} error={error} />
    </div>
  );
}
