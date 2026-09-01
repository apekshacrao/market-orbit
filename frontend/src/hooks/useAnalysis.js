import { useState, useEffect } from 'react';
import resultsApi from '../api/resultsApi';

export function useAnalysis(datasetId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!datasetId) return;
    setLoading(true);
    resultsApi.getAnalysisResults(datasetId)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [datasetId]);

  return { data, loading, error };
}
