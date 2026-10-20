import { useState } from 'react';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export default function Register() {
  const { register, loading, error } = useAuth();
  const [created, setCreated] = useState(false);

  const handleRegister = async (userData) => {
    try {
      await register(userData);
      setCreated(true);
    } catch {
      // The API error is shown by RegisterForm through useAuth.
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-story" aria-label="About Market Orbit">
        <a className="brand-lockup" href="/login" aria-label="Market Orbit home"><span className="brand-mark" aria-hidden="true">M</span><span>MARKET <b>ORBIT</b></span></a>
        <div className="story-copy">
          <p className="overline">A BETTER VIEW OF YOUR CAMPAIGNS</p>
          <h1>Clarity for<br /><em>what comes next.</em></h1>
          <p>Market Orbit connects the numbers to the decisions behind them, so your next move feels considered.</p>
        </div>
        <div className="story-visual" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-core"><span>MO</span></div><div className="visual-caption"><span className="status-dot" /> Your data, thoughtfully organized</div></div>
        <p className="auth-footnote">A calmer way to read the numbers.</p>
      </section>
      <section className="auth-panel">
        <div className="auth-form-container">
          {created ? (
            <div className="registration-success" role="status">
              <span className="success-mark" aria-hidden="true">✓</span>
              <p className="form-eyebrow">ACCOUNT CREATED</p>
              <h2>You’re ready to sign in.</h2>
              <p className="form-intro">Your account was created by the Market Orbit API. Continue to sign in with your new credentials.</p>
              <a className="button button-primary button-wide button-link" href="/login?registered=1">Continue to sign in</a>
            </div>
          ) : <RegisterForm onSubmit={handleRegister} loading={loading} error={error} />}
          <p className="security-note"><span aria-hidden="true">◆</span> Your workspace is private to your account.</p>
        </div>
      </section>
    </main>
  );
}
