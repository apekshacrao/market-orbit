export default function AiRecommendations({ recommendations = [] }) {
  return (
    <section className="panel recommendations-panel">
      <div className="panel-heading"><div><p className="eyebrow">FROM YOUR ANALYSIS</p><h2>Recommendations</h2><p className="panel-subtitle">Actions grounded in this dataset’s performance.</p></div><span className="panel-icon gold" aria-hidden="true">✳</span></div>
      {!recommendations.length ? <p className="panel-empty">Recommendations are not available for this dataset yet.</p> : <div className="recommendations-list">
        {recommendations.map((recommendation, index) => <article className="recommendation-card" key={recommendation.id || `${recommendation.title}-${index}`}>
          <div className="recommendation-index">{String(index + 1).padStart(2, '0')}</div>
          <div className="recommendation-copy"><div className="recommendation-meta">{recommendation.category || 'INSIGHT'}</div><h3>{recommendation.title || 'Marketing insight'}</h3><p>{recommendation.rationale || recommendation.description || 'The analysis did not include an explanation for this recommendation.'}</p>{recommendation.action && <div className="recommendation-action"><span>Suggested action</span><strong>{recommendation.action}</strong></div>}</div>
        </article>)}
      </div>}
    </section>
  );
}
