import React from 'react';

export default function PerformanceChart({ data = [] }) {
  return (
    <div className="performance-chart-wrapper">
      <h3>Campaign Performance Overview</h3>
      <div className="chart-placeholder">
        <p>Performance chart visualization ({data.length} data points)</p>
      </div>
    </div>
  );
}
