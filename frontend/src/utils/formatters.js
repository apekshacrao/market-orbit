export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
}

export function formatPercentage(value) {
  return `${((value || 0) * 100).toFixed(2)}%`;
}

export function formatNumber(num) {
  return new Intl.NumberFormat('en-US').format(num || 0);
}

export function formatDate(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
