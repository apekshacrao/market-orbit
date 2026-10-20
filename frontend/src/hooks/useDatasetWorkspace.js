import { useEffect, useState } from 'react';
import uploadApi from '../api/uploadApi';

export function useDatasetWorkspace() {
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    uploadApi.getDatasets().then((items) => {
      if (!active) return;
      const list = Array.isArray(items) ? items : [];
      setDatasets(list);
      const requested = new URLSearchParams(window.location.search).get('dataset_id') || localStorage.getItem('dataset_id');
      const selected = requested && list.some((item) => item.id === requested) ? requested : (list[0]?.id || '');
      setDatasetId(selected);
      if (selected) localStorage.setItem('dataset_id', selected);
    }).catch((e) => { if (active) setError(e.message || 'Could not load datasets.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refreshKey]);
  const selectDataset = (id) => { setDatasetId(id); if (id) localStorage.setItem('dataset_id', id); };
  return { datasets, datasetId, selectDataset, selectedDataset: datasets.find((item) => item.id === datasetId), loading, error, refresh: () => setRefreshKey((n) => n + 1) };
}
