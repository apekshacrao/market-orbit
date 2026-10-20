import { useRef, useState } from 'react';

export default function FileDropzone({ onFileSelected, disabled = false }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);
  const openPicker = () => { if (!disabled) inputRef.current?.click(); };

  return (
    <div
      className={`file-dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'dropzone-disabled' : ''}`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      aria-label="Choose or drop a CSV dataset"
      onClick={openPicker}
      onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openPicker(); } }}
      onDragEnter={(event) => { event.preventDefault(); if (!disabled) setIsDragging(true); }}
      onDragOver={(event) => { event.preventDefault(); if (!disabled) setIsDragging(true); }}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setIsDragging(false); }}
      onDrop={(event) => { event.preventDefault(); setIsDragging(false); if (!disabled && event.dataTransfer.files?.[0]) onFileSelected(event.dataTransfer.files[0]); }}
    >
      <input ref={inputRef} className="file-input-hidden" type="file" accept=".csv,text/csv" aria-label="Select CSV file" disabled={disabled} onClick={(event) => event.stopPropagation()} onChange={(event) => { if (event.target.files?.[0]) onFileSelected(event.target.files[0]); event.target.value = ''; }} />
      <span className="dropzone-icon" aria-hidden="true"><span>↑</span></span>
      <strong>Drop your CSV file here</strong>
      <span className="dropzone-copy">or <span className="dropzone-browse">browse files</span> from your device</span>
      <span className="dropzone-format"><span className="csv-badge">CSV</span> Comma-separated values only</span>
    </div>
  );
}
