import { useEffect, useState } from 'react';
import resultsApi from '../api/resultsApi';

export function useAnalysis(datasetId, refreshKey = 0) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(datasetId));
  const [error, setError] = useState('');

  useEffect(() => {
    if (!datasetId) {
      setData(null);
      setLoading(false);
      setError('');
      return undefined;
    }

    let active = true;
    setLoading(true);
    setError('');
    resultsApi.getAnalysisResults(datasetId)
      .then((result) => { if (active) setData(result); })
      .catch((requestError) => { if (active) { setData(null); setError(requestError.message); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [datasetId, refreshKey]);

  return { data, loading, error };
}
