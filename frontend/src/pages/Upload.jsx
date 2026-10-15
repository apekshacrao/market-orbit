import React, { useState } from 'react';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (!selectedFile) return;

    const allowedExtensions = ['csv', 'xlsx', 'xls'];
    const extension = selectedFile.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setFile(null);
      setError('Please select a CSV or Excel file.');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

 return (
  <div className="dashboard-page">
    <Navbar />

    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-content">
        <div className="upload-page">
          <h1>Upload Marketing Data</h1>

          <p className="upload-description">
            Upload your campaign data to discover actionable marketing insights.
          </p>

          <div className="upload-card">
            <div className="upload-icon">↑</div>

            <h2>Choose your dataset</h2>

            <p>Supported formats: CSV, XLSX and XLS</p>

            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
            />

            {error && (
              <p className="upload-error">{error}</p>
            )}

           {file && (
  <div className="selected-file-card">
    <div>
      <strong>{file.name}</strong>
      <p>{(file.size / 1024).toFixed(2)} KB</p>
    </div>

    <button
      type="button"
      className="remove-file-button"
      onClick={() => {
        setFile(null);
        setError('');
      }}
    >
      Remove
    </button>
  </div>
)}

<button
  type="button"
  className="upload-button"
  disabled={!file}
  onClick={() => {
    alert('Backend upload integration is coming soon!');
  }}
>
  Upload Dataset
</button>

          </div>
        </div>
      </main>
    </div>
  </div>
);
}