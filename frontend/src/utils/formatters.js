export function formatCurrency(amount) {
  if (amount == null || !Number.isFinite(Number(amount))) return 'Unavailable';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(amount));
}

export function formatPercentage(value) {
  if (value == null || !Number.isFinite(Number(value))) return 'Unavailable';
  return `${(Number(value) * 100).toFixed(2)}%`;
}

export function formatNumber(num) {
  if (num == null || !Number.isFinite(Number(num))) return 'Unavailable';
  return new Intl.NumberFormat('en-US').format(Number(num));
}

export function formatDate(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
