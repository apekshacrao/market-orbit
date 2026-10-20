const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const pendingGets = new Map();

function describeDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || String(item)).filter(Boolean).join('; ');
  }
  if (detail && typeof detail === 'object') {
    const errors = Array.isArray(detail.errors)
      ? detail.errors.map((item) => {
        if (typeof item === 'string') return item;
        const where = [item.row != null ? `Row ${item.row}` : '', item.column || ''].filter(Boolean).join(', ');
        return [where, item.message || item.msg].filter(Boolean).join(': ');
      }).filter(Boolean).join('; ')
      : '';
    return [detail.message, errors].filter(Boolean).join(': ');
  }
  return '';
}

async function sendRequest(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers = new Headers(options.headers || {});
  if (options.body && !isFormData && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  } catch {
    throw new Error('The API could not be reached. Check that the backend is running, then retry.');
  }

  if (response.status === 401 && token) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const statusMessages = {
      401: 'Your session has expired. Sign in again.',
      403: 'You do not have access to this resource.',
      404: 'The requested dataset or resource was not found.',
      413: 'This file is too large for the server to accept.',
      422: 'The request could not be validated. Check the details and try again.',
    };
    const error = new Error(describeDetail(payload?.detail) || statusMessages[response.status] || `Request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') || '';
  return contentType.includes('application/json') ? response.json() : null;
}

export function apiClient(endpoint, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET') return sendRequest(endpoint, options);
  const key = `${localStorage.getItem('token') || ''}:${endpoint}`;
  if (pendingGets.has(key)) return pendingGets.get(key);
  const request = sendRequest(endpoint, options).finally(() => pendingGets.delete(key));
  pendingGets.set(key, request);
  return request;
}

export default apiClient;
