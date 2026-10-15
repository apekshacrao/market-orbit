import React from 'react';

const sampleRecommendations = [
  {
    title: 'Improve Social Campaign ROAS',
    description:
      'Your social campaigns have room for improvement. Review audience targeting and focus spending on creatives that generate more revenue.',
    action: 'Optimise social ad targeting'
  },
  {
    title: 'Increase High-Performing Campaign Spend',
    description:
      'Identify campaigns with consistently strong returns and consider reallocating budget towards them.',
    action: 'Review campaign budgets'
  },
  {
    title: 'Improve Conversion Rates',
    description:
      'Review landing pages and the customer journey to identify where potential customers are dropping off.',
    action: 'Optimise landing pages'
  }
];

export default function AiRecommendations({ recommendations }) {
  const items = recommendations?.length
    ? recommendations
    : sampleRecommendations;

  return (
    <section className="ai-recommendations-container">
      <h3>AI-Powered Insights &amp; Recommendations</h3>

      <p className="recommendations-description">
        Suggested actions to improve marketing performance.
      </p>

      <div className="recommendations-list">
        {items.map((rec, index) => (
          <article
            key={rec.title || index}
            className="recommendation-card"
          >
            <div className="recommendation-number">
              {String(index + 1).padStart(2, '0')}
            </div>

            <div className="recommendation-content">
              <h4>{rec.title}</h4>
              <p>{rec.description}</p>

              {rec.action && (
                <span className="action-tag">
                  Action: {rec.action}
                </span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}