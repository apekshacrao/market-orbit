import { useEffect, useState } from 'react';
import WorkspacePage, { logout } from '../components/common/WorkspacePage';

const MOTION_KEY = 'market-orbit-reduced-motion';

export default function Settings({ user }) {
  const [reduced, setReduced] = useState(() => localStorage.getItem(MOTION_KEY) === 'true');
  useEffect(() => {
    document.documentElement.classList.toggle('reduce-motion', reduced);
    localStorage.setItem(MOTION_KEY, String(reduced));
  }, [reduced]);
  const name = user?.name || user?.full_name || '';
  const email = user?.email || '';
  const initials = (name || email || 'MO').split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('');

  return <WorkspacePage user={user}>
    <div className="page-heading settings-heading">
      <div><p className="eyebrow">WORKSPACE PREFERENCES</p><h1>Settings</h1><p>Manage your profile, preferences, and account.</p></div>
    </div>
    <div className="settings-layout">
      <section className="settings-section" aria-labelledby="settings-profile">
        <div className="settings-section-heading"><div><h2 id="settings-profile">Profile</h2><p>Your account details from the signed-in session.</p></div></div>
        <div className="settings-profile-content">
          <span className="profile-avatar" aria-hidden="true">{initials || 'MO'}</span>
          <dl className="profile-details">
            <div><dt>Name</dt><dd>{name || 'Not provided'}</dd></div>
            <div><dt>Email</dt><dd>{email || 'Not provided'}</dd></div>
          </dl>
        </div>
        <p className="settings-note">Profile details are read-only because the backend does not provide a profile update endpoint.</p>
      </section>

      <section className="settings-section" aria-labelledby="settings-preferences">
        <div className="settings-section-heading"><div><h2 id="settings-preferences">Preferences</h2><p>Adjust how the workspace behaves in this browser.</p></div></div>
        <div className="preference-row theme-preview"><div><strong>Orbit workspace theme</strong><small>Cool neutral surfaces with clear blue actions.</small></div></div>
        <label className="setting-toggle"><span><strong>Reduce motion</strong><small>Limit interface animations and transitions.</small></span><input type="checkbox" checked={reduced} onChange={(event) => setReduced(event.target.checked)} aria-label="Reduce motion"/><i/></label>
        <p className="settings-note">The reduced-motion preference is saved in this browser.</p>
      </section>

      <section className="settings-section account-session" aria-labelledby="settings-session">
        <div className="settings-section-heading"><div><h2 id="settings-session">Account and session</h2><p>End your current Market Orbit session.</p></div></div>
        <p className="session-state"><span className="status-dot"/> Signed in as {email || 'authenticated user'}</p>
        <p className="settings-note">Password changes and other security controls are not available in the current backend.</p>
        <button className="button button-secondary" onClick={logout}>Sign out</button>
      </section>
    </div>
  </WorkspacePage>;
}
