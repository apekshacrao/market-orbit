import { useState, useEffect } from 'react';
import resultsApi from '../api/resultsApi';

export function useAnalysis(datasetId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(datasetId));
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    if (!datasetId) {
      setData(null);
      setError(null);
      setLoading(false);
      return undefined;
    }
    setData(null);
    setError(null);
    setLoading(true);
    resultsApi.getAnalysisResults(datasetId)
      .then((result) => { if (active) setData(result); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [datasetId]);

  return { data, loading, error };
}
