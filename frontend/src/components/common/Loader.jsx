import React from 'react';

export default function Loader({ message = 'Loading...' }) {
  return (
    <div className="loader-container" role="status" aria-live="polite" aria-busy="true">
      <span className="loader-message">{message}</span>
      <div className="loader-skeleton" aria-hidden="true">
        <i className="skeleton-line loader-skeleton-line wide" />
        <i className="skeleton-line loader-skeleton-line medium" />
        <i className="skeleton-line loader-skeleton-line short" />
      </div>
    </div>
  );
}
