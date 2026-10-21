import React from 'react';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export default function Register() {
  const { register, loading, error } = useAuth();
  const handleRegister = async (userData) => {
    try {
      await register(userData);
      window.location.assign('/login?registered=1');
    } catch {
      // The hook exposes the API error to the form.
    }
  };

  return (
    <main className="page-container auth-page">
      <div className="auth-brand">
        <h1>Market Orbit</h1>
        <p>Turn your marketing data into clear, actionable insights.</p>
      </div>
      <div className="auth-form-container">
        <RegisterForm onSubmit={handleRegister} loading={loading} error={error} />
      </div>
    </main>
  );
}
