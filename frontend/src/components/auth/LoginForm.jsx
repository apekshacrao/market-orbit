import React, { useState } from 'react';

export default function LoginForm({ onSubmit, loading, error }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onSubmit({ email: email.trim(), password });
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <h2>Sign In</h2>
      {error && <div id="login-error" className="error-message" role="alert">{error}</div>}
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          aria-describedby={error ? 'login-error' : undefined}
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>

      <p className="auth-switch">
        Don't have an account?{' '}
        <a href="/register">Create one</a>
      </p>
    </form>
  );
}
