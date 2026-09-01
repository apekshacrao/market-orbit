export function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
}

export function isValidPassword(password) {
  return typeof password === 'string' && password.length >= 8;
}

export function validateFileType(file, allowedExtensions = ['.csv', '.xlsx', '.xls']) {
  if (!file) return false;
  return allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
}
