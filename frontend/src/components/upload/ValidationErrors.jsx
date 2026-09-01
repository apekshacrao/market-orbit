import React from 'react';

export default function ValidationErrors({ errors = [] }) {
  if (!errors || errors.length === 0) return null;

  return (
    <div className="validation-errors">
      <h3>Validation Issues Detected</h3>
      <ul>
        {errors.map((error, idx) => (
          <li key={idx} className="error-item">
            <strong>Row {error.row || 'N/A'}:</strong> {error.message || error}
          </li>
        ))}
      </ul>
    </div>
  );
}
