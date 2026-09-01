import apiClient from './client';

export const resultsApi = {
  getAnalysisResults: (datasetId) => apiClient(`/results/${datasetId}`),
  getKpiSummary: (datasetId) => apiClient(`/results/${datasetId}/kpis`),
  getCampaignRankings: (datasetId) => apiClient(`/results/${datasetId}/rankings`),
  getRecommendations: (datasetId) => apiClient(`/results/${datasetId}/recommendations`),
};

export default resultsApi;
