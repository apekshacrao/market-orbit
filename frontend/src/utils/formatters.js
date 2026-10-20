export function formatAmount(value) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value));
}

export function formatPercentage(value) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return `${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

export function formatNumber(value) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return new Intl.NumberFormat('en-US').format(Number(value));
}

export function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(`${dateString}T00:00:00`);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}
