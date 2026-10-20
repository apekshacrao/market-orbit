import { useState } from 'react';

export default function RegisterForm({ onSubmit, loading, error }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (password !== confirmation) {
      setValidationError('Those passwords do not match. Check them and try again.');
      return;
    }
    setValidationError('');
    onSubmit({ name, email, password });
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="form-eyebrow">YOUR DATA, IN CONTEXT</div>
      <h2>Create your account</h2>
      <p className="form-intro">A clearer view of every campaign starts here.</p>
      {validationError && <div className="feedback feedback-error" role="alert">{validationError}</div>}
      {error && <div className="feedback feedback-error" role="alert">{error}</div>}
      <div className="form-group">
        <label htmlFor="register-name">Full name</label>
        <input id="register-name" name="name" type="text" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" required />
      </div>
      <div className="form-group">
        <label htmlFor="register-email">Email address</label>
        <input id="register-email" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required />
      </div>
      <div className="form-group">
        <label htmlFor="register-password">Password</label>
        <div className="password-field">
          <input id="register-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          <button className="field-action" type="button" onClick={() => setShowPassword((shown) => !shown)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? 'Hide' : 'Show'}</button>
        </div>
      </div>
      <div className="form-group">
        <label htmlFor="register-confirm">Confirm password</label>
        <input id="register-confirm" name="confirmation" type={showPassword ? 'text' : 'password'} autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} required />
      </div>
      <button className="button button-primary button-wide" type="submit" disabled={loading}>
        {loading ? <><span className="button-spinner" aria-hidden="true" /> Creating account…</> : 'Create account'}
      </button>
      <p className="auth-switch">Already have an account? <a href="/login">Sign in</a></p>
    </form>
  );
}
