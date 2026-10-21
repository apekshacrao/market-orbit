import React from 'react';

export default function AiRecommendations({ recommendations = [] }) {
  return (
    <section className="ai-recommendations-container">
      <div className="recommendations-heading"><div><p className="eyebrow">DECISION SUPPORT</p><h2>AI recommendations</h2><p className="recommendations-description">Prioritized actions based on the selected dataset.</p></div>{recommendations.length > 0 && <span className="record-count">{recommendations.length} suggestions</span>}</div>
      {recommendations.length ? (
        <div className="recommendations-list">
          {recommendations.map((rec, index) => (
            <article key={rec.id || rec.title || index} className="recommendation-card">
              <div className="recommendation-number">{String(index + 1).padStart(2, '0')}</div>
              <div className="recommendation-content">
                <h4>{rec.title || 'Recommendation'}</h4>
                <p>{rec.description || rec.reason || rec.rationale || 'No additional detail provided.'}</p>
                {rec.action && <span className="action-tag">Action: {rec.action}</span>}
                {rec.impact && <span className="recommendation-impact">Impact: {rec.impact}</span>}
              </div>
            </article>
          ))}
        </div>
      ) : <div className="recommendations-empty"><strong>No recommendations yet</strong><p>Refresh the analysis or review the campaign metrics and trends for this dataset.</p><a href="/graphs">Explore analytics</a></div>}
    </section>
  );
}
