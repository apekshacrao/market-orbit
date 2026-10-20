const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function apiClient(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    ...(options.body && !(options.body instanceof FormData) && { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  } catch {
    throw new Error('Unable to reach the API. Check that the backend is running and try again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    if (response.status === 401 && token) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') window.location.assign('/login');
    }
    const detail = errorData.detail;
    const validationMessages = Array.isArray(detail?.errors)
      ? detail.errors.map((item) => {
        if (typeof item === 'string') return item;
        const location = [item.row != null ? `Row ${item.row}` : null, item.column].filter(Boolean).join(', ');
        return [location, item.message || item.msg].filter(Boolean).join(': ');
      }).filter(Boolean)
      : [];
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item.msg || item.message).filter(Boolean).join('; ')
        : [detail?.message, ...validationMessages].filter(Boolean).join(': ');
    const statusMessage = {
      401: 'Your session has expired. Please sign in again.',
      403: 'You do not have access to this dataset.',
      404: 'The requested dataset was not found.',
      422: 'The uploaded CSV could not be validated.',
    }[response.status];
    const error = new Error(message || statusMessage || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}

export default apiClient;
