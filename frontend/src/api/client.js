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
    const detail = typeof errorData.detail === 'string'
      ? errorData.detail
      : Array.isArray(errorData.detail)
        ? errorData.detail.map((item) => item.msg || item.message).filter(Boolean).join('; ')
        : errorData.detail?.message || `Request failed (${response.status})`;
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
}

export default apiClient;
