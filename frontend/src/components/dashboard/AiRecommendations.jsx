import React from 'react';

export default function AiRecommendations({ recommendations = [] }) {
  return (
    <section className="ai-recommendations-container">
      <h3>AI-Powered Insights &amp; Recommendations</h3>
      <p className="recommendations-description">Recommendations generated for this dataset.</p>
      {recommendations.length ? (
        <div className="recommendations-list">
          {recommendations.map((rec, index) => (
            <article key={rec.id || rec.title || index} className="recommendation-card">
              <div className="recommendation-number">{String(index + 1).padStart(2, '0')}</div>
              <div className="recommendation-content">
                <h4>{rec.title || 'Recommendation'}</h4>
                <p>{rec.description || rec.reason || 'No additional detail provided.'}</p>
                {rec.action && <span className="action-tag">Action: {rec.action}</span>}
                {rec.impact && <span className="recommendation-impact">Impact: {rec.impact}</span>}
              </div>
            </article>
          ))}
        </div>
      ) : <p className="empty-state">No recommendations are available for this dataset yet.</p>}
    </section>
  );
}
