import apiClient from './client';

export const resultsApi = {
  getAnalysisResults: (datasetId) => apiClient(`/results/${encodeURIComponent(datasetId)}`),
  getKpiSummary: (datasetId) => apiClient(`/results/${encodeURIComponent(datasetId)}/kpis`),
};

export default resultsApi;
