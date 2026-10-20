import { useState, useEffect } from 'react';
import resultsApi from '../api/resultsApi';

export function useAnalysis(datasetId) {
  const [request, setRequest] = useState({ datasetId: null, data: null, loading: false, error: null });

  useEffect(() => {
    let active = true;
    if (!datasetId) {
      setRequest({ datasetId: null, data: null, loading: false, error: null });
      return undefined;
    }

    setRequest({ datasetId, data: null, loading: true, error: null });
    resultsApi.getAnalysisResults(datasetId)
      .then((data) => {
        if (active) setRequest({ datasetId, data, loading: false, error: null });
      })
      .catch((err) => {
        if (active) setRequest({ datasetId, data: null, loading: false, error: err.message });
      });
    return () => { active = false; };
  }, [datasetId]);

  if (request.datasetId !== datasetId) {
    return { data: null, loading: Boolean(datasetId), error: null };
  }
  return { data: request.data, loading: request.loading, error: request.error };
}
