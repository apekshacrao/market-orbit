export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('dataset_id');
  window.location.assign('/login');
}
