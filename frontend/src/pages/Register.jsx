import React, { useState } from 'react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();

    console.log({
      name,
      email,
      password
    });
  };

  return (
    <div className="page-container auth-page">
      <div className="auth-brand">
        <h1>Market Orbit</h1>
        <p>
          Turn your marketing data into clear,
          actionable insights.
        </p>
      </div>

      <div className="auth-form-container">
        <form className="login-form" onSubmit={handleSubmit}>
          <h2>Create Account</h2>
          <p className="auth-switch">
            Already have an account?{' '}
            <a href="/">Sign in</a>
          </p>
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a password"
              required
            />
          </div>

          <button type="submit">
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}