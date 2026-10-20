import Navbar from './Navbar';
import Sidebar from './Sidebar';

export function logout() {
  localStorage.removeItem('token'); localStorage.removeItem('user'); localStorage.removeItem('dataset_id');
  window.location.assign('/login');
}

export default function WorkspacePage({ user, datasetName, children }) {
  return <div className="dashboard-page"><Navbar user={user} datasetName={datasetName} onLogout={logout} /><div className="dashboard-layout"><Sidebar user={user} onLogout={logout} /><main className="dashboard-content">{children}</main></div></div>;
}
