import React from 'react';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

export default function Register() {
  const { register, loading, error } = useAuth();

  return (
    <div className="page-container auth-page">
      <RegisterForm onSubmit={register} loading={loading} error={error} />
    </div>
  );
}
