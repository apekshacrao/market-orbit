import React from 'react';

export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="error-message-box">
      <p>{message}</p>
      {onRetry && <button type="button" onClick={onRetry}>Retry</button>}
    </div>
  );
}
