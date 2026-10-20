import apiClient from './client';

export const uploadApi = {
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient('/uploads/', { method: 'POST', body: formData });
  },
  getDatasets: () => apiClient('/uploads/'),
  getUploadStatus: (datasetId) => apiClient(`/uploads/${encodeURIComponent(datasetId)}/status`),
  getDatasetCampaigns: (datasetId) => apiClient(`/uploads/${encodeURIComponent(datasetId)}/campaigns`),
};

export default uploadApi;
