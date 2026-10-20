export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim().toLowerCase());
}

export function validateFileType(file) {
  return Boolean(file?.name?.toLowerCase().endsWith('.csv'));
}

function splitCsvHeader(line) {
  const fields = [];
  let value = '';
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"' && line[index + 1] === '"' && inQuotes) {
      value += '"';
      index += 1;
    } else if (character === '"') {
      inQuotes = !inQuotes;
    } else if (character === ',' && !inQuotes) {
      fields.push(value.trim());
      value = '';
    } else {
      value += character;
    }
  }
  fields.push(value.trim());
  return fields;
}

export async function validateCsvFile(file) {
  if (!file) return ['Choose a CSV file to continue.'];
  if (!validateFileType(file)) return ['The backend accepts CSV files only. Choose a .csv file.'];
  try {
    const headerText = (await file.slice(0, 65536).text()).split(/\r?\n/, 1)[0].replace(/^\uFEFF/, '');
    if (!headerText.trim()) return ['This CSV file is empty or has no header row.'];
    const columns = new Set(splitCsvHeader(headerText));
    const required = ['campaign_name', 'channel', 'spend', 'conversions'];
    const missing = required.filter((column) => !columns.has(column));
    return missing.length ? [`Missing required column${missing.length > 1 ? 's' : ''}: ${missing.join(', ')}.`] : [];
  } catch {
    return ['The file could not be read. Choose another CSV file.'];
  }
}
