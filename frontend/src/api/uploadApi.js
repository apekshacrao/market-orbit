import apiClient from './client';

export const uploadApi = {
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient('/uploads/', { method: 'POST', body: formData });
  },
  getUploadStatus: (datasetId) => apiClient(`/uploads/${encodeURIComponent(datasetId)}/status`),
  getDatasets: () => apiClient('/uploads/'),
};

export default uploadApi;
