import React, { useState } from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import uploadApi from '../api/uploadApi';
import FileDropzone from '../components/upload/FileDropzone';

export default function Upload({ user }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadedDataset, setUploadedDataset] = useState(null);

  const selectFile = (selectedFile) => {
    setUploadedDataset(null);
    setFile(selectedFile);
    setError('');
  };

  const handleUpload = async () => {
    if (!file || loading) return;
    setLoading(true);
    setError('');
    try {
      const result = await uploadApi.uploadFile(file);
      setUploadedDataset(result);
      if (result.dataset_id) localStorage.setItem('dataset_id', result.dataset_id);
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-page">
      <Navbar user={user} />
      <div className="dashboard-layout">
        <Sidebar user={user} />
        <main className="dashboard-content">
          <div className="upload-page">
            <div className="page-heading upload-heading"><div><p className="eyebrow">GET STARTED</p><h1>Upload a dataset</h1><p>Bring in campaign data to explore performance and get recommendations.</p></div></div>
            <div className="upload-card">
              <div className="upload-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5"/><path d="M5 14v5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5"/></svg></div>
              <h2>Choose a CSV file</h2>
              <p>Upload campaign rows as a .csv file. Your file is used to generate this workspace’s analytics.</p>
              <FileDropzone onFileSelected={selectFile} disabled={loading} />
              <div className="upload-requirements"><div><strong>Required columns</strong><span>campaign_name, channel, spend, conversions</span></div><div><strong>Recommended for trend charts</strong><span>date, revenue</span></div><div><strong>Optional metrics</strong><span>clicks, impressions</span></div></div>
              {error && <p className="upload-error" role="alert">{error}</p>}
              {file && (
                <div className="selected-file-card">
                  <div><strong>{file.name}</strong><p>{(file.size / 1024).toFixed(2)} KB</p></div>
                  <button type="button" className="remove-file-button" disabled={loading} onClick={() => { setFile(null); setError(''); }}>Remove</button>
                </div>
              )}
              <button type="button" className="upload-button" disabled={!file || loading} onClick={handleUpload}>
                {loading ? 'Uploading and processing…' : 'Upload Dataset'}
              </button>
              {uploadedDataset && (
                <div className="upload-success" role="status">
                  <p><strong>Your dataset is ready to explore.</strong></p>
                  <p>{uploadedDataset.filename} · Processing status: {uploadedDataset.status}</p>
                  <a className="primary-link-button" href={`/dashboard?dataset_id=${encodeURIComponent(uploadedDataset.dataset_id)}`}>Open this dataset</a>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
