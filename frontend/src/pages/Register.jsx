import React, { useState } from 'react';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export default function Register() {
  const { register, loading, error } = useAuth();
  const [success, setSuccess] = useState(false);
  const handleRegister = async (userData) => {
    try {
      await register(userData);
      setSuccess(true);
    } catch {
      // The hook exposes the API error to the form.
    }
  };

  return (
    <div className="page-container auth-page">
      <div className="auth-brand">
        <h1>Market Orbit</h1>
        <p>Turn your marketing data into clear, actionable insights.</p>
      </div>
      <div className="auth-form-container">
        {success ? (
          <div role="status" className="success-message">
            <h2>Account created</h2>
            <p>Your account is ready. Sign in to continue.</p>
            <a className="primary-link-button" href="/login">Go to sign in</a>
          </div>
        ) : (
          <RegisterForm onSubmit={handleRegister} loading={loading} error={error} />
        )}
      </div>
    </div>
  );
}
