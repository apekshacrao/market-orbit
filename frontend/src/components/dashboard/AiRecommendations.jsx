import React from 'react';

export default function AiRecommendations({ recommendations = [] }) {
  return (
    <div className="ai-recommendations-container">
      <h3>AI-Powered Insights & Recommendations</h3>
      {recommendations.length === 0 ? (
        <p>No recommendations generated yet.</p>
      ) : (
        <div className="recommendations-list">
          {recommendations.map((rec, index) => (
            <div key={index} className="recommendation-card">
              <h4>{rec.title}</h4>
              <p>{rec.description}</p>
              {rec.action && <span className="action-tag">Action: {rec.action}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
