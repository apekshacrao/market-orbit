import React, { useState } from 'react';
import FileDropzone from '../components/upload/FileDropzone';
import UploadProgress from '../components/upload/UploadProgress';
import ValidationErrors from '../components/upload/ValidationErrors';
import uploadApi from '../api/uploadApi';

export default function Upload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errors, setErrors] = useState([]);

  const handleFile = async (file) => {
    setUploading(true);
    setProgress(20);
    try {
      await uploadApi.uploadFile(file);
      setProgress(100);
    } catch (err) {
      setErrors([{ message: err.message }]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-container upload-page">
      <h2>Upload Marketing Campaign Data</h2>
      <FileDropzone onFileSelected={handleFile} disabled={uploading} />
      {uploading && <UploadProgress progress={progress} />}
      <ValidationErrors errors={errors} />
    </div>
  );
}
