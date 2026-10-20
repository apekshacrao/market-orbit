import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const { login, loading, error } = useAuth();
  const registered = new URLSearchParams(window.location.search).get('registered') === '1';

  const handleLogin = async (credentials) => {
    try {
      await login(credentials);
      window.location.assign('/dashboard');
    } catch {
      // The API error is shown by LoginForm through useAuth.
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-story" aria-label="About Market Orbit">
        <a className="brand-lockup" href="/login" aria-label="Market Orbit home"><span className="brand-mark" aria-hidden="true">M</span><span>MARKET <b>ORBIT</b></span></a>
        <div className="story-copy">
          <p className="overline">MARKETING INTELLIGENCE, WITH CLARITY</p>
          <h1>Make every<br /><em>signal</em> count.</h1>
          <p>Bring your campaign data into focus. Understand what is working, where spend goes further, and what to do next.</p>
        </div>
        <div className="story-visual" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-core"><span>MO</span></div>
          <div className="visual-caption"><span className="status-dot" /> Built for thoughtful growth</div>
        </div>
        <p className="auth-footnote">A calmer way to read the numbers.</p>
      </section>
      <section className="auth-panel">
        <div className="auth-form-container">
          {registered && <div className="feedback feedback-success" role="status">Your account was created. Sign in to continue.</div>}
          <LoginForm onSubmit={handleLogin} loading={loading} error={error} />
          <p className="security-note"><span aria-hidden="true">◆</span> Your workspace is private to your account.</p>
        </div>
      </section>
    </main>
  );
}
