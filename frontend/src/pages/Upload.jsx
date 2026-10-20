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
            <h1>Upload Dataset</h1>
            <p className="upload-description">Upload campaign data to calculate performance and recommendations.</p>
            <div className="upload-card">
              <div className="upload-icon" aria-hidden="true">↑</div>
              <h2>Choose your dataset</h2>
              <p>CSV files only, as supported by the upload API.</p>
              <FileDropzone onFileSelected={selectFile} disabled={loading} />
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
                  <p><strong>{uploadedDataset.message || 'Upload confirmed.'}</strong></p>
                  <p>{uploadedDataset.filename} · Status: {uploadedDataset.status}</p>
                  <a className="primary-link-button" href={`/dashboard?dataset_id=${encodeURIComponent(uploadedDataset.dataset_id)}`}>View dataset dashboard</a>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
