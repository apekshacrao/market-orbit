import React from 'react';

export default function UploadProgress({ progress, statusText }) {
  return (
    <div className="upload-progress">
      <div className="progress-bar-container">
        <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      </div>
      <div className="progress-info">
        <span>{statusText || 'Processing dataset...'}</span>
        <span>{progress}%</span>
      </div>
    </div>
  );
}
