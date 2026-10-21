import React from 'react';

export default function DatasetSelector({ datasets = [], datasetId = '', onChange, disabled = false }) {
  if (!datasets.length) return null;
  return <label className="dataset-picker compact-dataset-picker">
    <span>Dataset</span>
    <select aria-label="Selected dataset" value={datasetId} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
      {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.filename}</option>)}
    </select>
  </label>;
}
