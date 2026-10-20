export default function ValidationErrors({ errors = [] }) {
  if (!errors.length) return null;
  return <div className="feedback feedback-error upload-feedback" role="alert"><strong>We couldn’t use that file.</strong><ul>{errors.map((error, index) => <li key={index}>{typeof error === 'string' ? error : error.message || 'Check the selected file and try again.'}</li>)}</ul></div>;
}
