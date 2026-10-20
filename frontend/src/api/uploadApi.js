import apiClient from './client';

export const uploadApi = {
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient('/uploads/', { method: 'POST', body: formData });
  },
  getUploadStatus: (datasetId) => apiClient(`/uploads/${encodeURIComponent(datasetId)}/status`),
  getDatasetCampaigns: (datasetId) => apiClient(`/uploads/${encodeURIComponent(datasetId)}/campaigns`),
  getDatasets: () => apiClient('/uploads/'),
};

export default uploadApi;
