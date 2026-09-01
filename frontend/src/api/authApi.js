import apiClient from './client';

export const authApi = {
  login: (credentials) => apiClient('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }),

  register: (userData) => apiClient('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  }),

  getCurrentUser: () => apiClient('/auth/me'),
};

export default authApi;
