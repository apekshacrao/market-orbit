import { useState } from 'react';

export default function LoginForm({ onSubmit, loading, error }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({ email, password });
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="form-eyebrow">WELCOME BACK</div>
      <h2>Sign in to your workspace</h2>
      <p className="form-intro">See what your marketing data is telling you.</p>
      {error && <div className="feedback feedback-error" role="alert">{error}</div>}
      <div className="form-group">
        <label htmlFor="login-email">Email address</label>
        <input id="login-email" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required />
      </div>
      <div className="form-group">
        <div className="label-row"><label htmlFor="login-password">Password</label></div>
        <div className="password-field">
          <input id="login-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" required />
          <button className="field-action" type="button" onClick={() => setShowPassword((shown) => !shown)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? 'Hide' : 'Show'}</button>
        </div>
      </div>
      <button className="button button-primary button-wide" type="submit" disabled={loading}>
        {loading ? <><span className="button-spinner" aria-hidden="true" /> Signing in…</> : 'Sign in'}
      </button>
      <p className="auth-switch">New to Market Orbit? <a href="/register">Create an account</a></p>
    </form>
  );
}
