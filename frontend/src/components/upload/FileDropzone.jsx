import React, { useState } from 'react';

export default function FileDropzone({ onFileSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const selectFile = (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('The backend accepts CSV files only. Please choose a .csv file.');
      return;
    }
    setError('');
    onFileSelected(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      selectFile(files[0]);
    }
  };

  return (
    <>
    <label
      className={`file-dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        id="campaign-csv-file"
        className="visually-hidden file-dropzone-input"
        type="file"
        accept=".csv,text/csv"
        aria-label="Choose a CSV campaign data file"
        aria-describedby="file-dropzone-help"
        disabled={disabled}
        onChange={(e) => {
          selectFile(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      <span className="file-dropzone-instruction">Drag and drop your marketing campaign CSV file here, or click to browse</span>
      <span id="file-dropzone-help">Supported format: CSV</span>
    </label>
    {error && <p className="upload-error" role="alert">{error}</p>}
    </>
  );
}
