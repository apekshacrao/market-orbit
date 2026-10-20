import { useState } from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import FileDropzone from '../components/upload/FileDropzone';
import ValidationErrors from '../components/upload/ValidationErrors';
import uploadApi from '../api/uploadApi';
import { validateCsvFile } from '../utils/validation';

function fileSize(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('dataset_id');
  window.location.assign('/login');
}

export default function Upload({ user }) {
  const [file, setFile] = useState(null);
  const [errors, setErrors] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const selectFile = async (selected) => {
    setResult(null);
    setErrors([]);
    const validation = await validateCsvFile(selected);
    if (validation.length) {
      setFile(null);
      setErrors(validation);
      return;
    }
    setFile(selected);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setErrors([]);
    setResult(null);
    try {
      const response = await uploadApi.uploadFile(file);
      if (!response?.dataset_id) throw new Error('The server response did not include a dataset ID. Please refresh your dataset list before trying again.');
      localStorage.setItem('dataset_id', response.dataset_id);
      setResult(response);
    } catch (error) {
      setErrors([error.message || 'Upload failed. Check your connection and try again.']);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="dashboard-page">
      <Navbar user={user} onLogout={logout} />
      <div className="dashboard-layout"><Sidebar user={user} onLogout={logout} />
        <main className="dashboard-content upload-content">
          <div className="page-heading"><div><p className="eyebrow">DATA WORKSPACE</p><h1>Upload marketing dataset</h1><p>Bring campaign performance into Market Orbit for analysis.</p></div><span className="heading-index">01 <i>/</i> 02</span></div>
          <div className="upload-layout">
            <section className="panel upload-workspace">
              <div className="upload-step"><span className="step-number">01</span><div><h2>Select your CSV</h2><p>Choose the campaign data you want to explore.</p></div></div>
              <FileDropzone onFileSelected={selectFile} disabled={uploading} />
              {file && <div className="selected-file-card"><span className="file-type-icon" aria-hidden="true">CSV</span><div className="selected-file-copy"><strong title={file.name}>{file.name}</strong><span>{fileSize(file.size)} · Ready to upload</span></div><button className="text-button" type="button" disabled={uploading} onClick={() => { setFile(null); setErrors([]); setResult(null); }}>Remove</button></div>}
              <ValidationErrors errors={errors} />
              {uploading && <div className="upload-activity" role="status"><span className="button-spinner" aria-hidden="true" /> Sending file to the analysis service…</div>}
              {result && <div className="upload-success" role="status"><span className="success-mark" aria-hidden="true">✓</span><div><strong>Dataset received</strong><span>{result.filename} · {result.status}</span><small>Dataset ID: <code>{result.dataset_id}</code></small></div><a className="button button-primary button-compact" href={`/dashboard?dataset_id=${encodeURIComponent(result.dataset_id)}`}>View analysis <span aria-hidden="true">↗</span></a></div>}
              <button className="button button-primary button-wide upload-submit" type="button" disabled={!file || uploading} onClick={handleUpload}>{uploading ? 'Uploading…' : 'Upload dataset'}</button>
            </section>
            <aside className="upload-guidance">
              <section className="panel guidance-panel"><p className="eyebrow">FILE REQUIREMENTS</p><h2>Keep the data clean.</h2><p>The backend accepts CSV files and checks each one before importing.</p><div className="requirement-list"><div><span className="requirement-check">✓</span><span><strong>Required columns</strong><small>campaign_name, channel, spend, conversions</small></span></div><div><span className="requirement-check">✓</span><span><strong>Optional context</strong><small>revenue, date, clicks, impressions and segments</small></span></div><div><span className="requirement-check">✓</span><span><strong>CSV format</strong><small>Export your spreadsheet as comma-separated values</small></span></div></div></section>
              <div className="privacy-note"><span aria-hidden="true">◇</span><p><strong>Private to your workspace</strong><br />Uploaded datasets are associated with your signed-in account.</p></div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}
