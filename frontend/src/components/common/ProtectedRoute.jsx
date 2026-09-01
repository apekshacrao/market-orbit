import React from 'react';

export default function ProtectedRoute({ isAuthenticated, children, fallback = null }) {
  if (!isAuthenticated) {
    return fallback;
  }
  return children;
}
