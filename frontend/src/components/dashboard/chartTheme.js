const chartTheme = {
  surface: 'var(--chart-surface)',
  border: 'var(--chart-border)',
  text: 'var(--chart-text)',
  muted: 'var(--chart-muted)',
  grid: 'var(--chart-grid)',
  series: {
    spend: 'var(--chart-series-spend)',
    revenue: 'var(--chart-series-revenue)',
    conversions: 'var(--chart-series-conversions)',
  },
};

export const chartTooltipStyle = {
  backgroundColor: chartTheme.surface,
  border: `1px solid ${chartTheme.border}`,
  borderRadius: '8px',
  color: chartTheme.text,
  boxShadow: '0 4px 14px rgba(37, 42, 48, 0.12)',
};

export const chartAxisStyle = { fontSize: 11 };
export default chartTheme;
