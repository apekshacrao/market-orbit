import React, { useState, useRef } from 'react';

export default function FileDropzone({ onFileSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

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
    <div
      className={`file-dropzone ${isDragging ? 'dragging' : ''}`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onKeyDown={(event) => {
        if (!disabled && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault();
          fileInputRef.current?.click();
        }
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        style={{ display: 'none' }}
        onClick={(event) => event.stopPropagation()}
        onChange={(e) => {
          selectFile(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      <p>Drag and drop your marketing campaign CSV file here, or click to browse</p>
      <span>Supported format: CSV</span>
      {error && <p className="upload-error" role="alert">{error}</p>}
    </div>
  );
}
