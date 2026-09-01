const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const uploadApi = {
  uploadFile: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');

    const response = await fetch(`${API_BASE_URL}/uploads/`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'File upload failed');
    }

    return response.json();
  },

  getUploadStatus: (uploadId) => {
    const token = localStorage.getItem('token');
    return fetch(`${API_BASE_URL}/uploads/${uploadId}/status`, {
      headers: { ...(token && { Authorization: `Bearer ${token}` }) },
    }).then(res => res.json());
  },
};

export default uploadApi;
