export function uuid() {
  return crypto.randomUUID()
}

// Timestamp compacto para nombres de archivo: 20260808T153045123
export function fileTimestamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, '').replace('.', '')
}
