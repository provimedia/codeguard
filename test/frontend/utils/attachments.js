// Attachment list helpers.

export function attachmentSummary(files) {
  return files.map((f) => `${f.name}: ${formatBytes(f.size)}`).join(', ');
}

/**
 * REDUNDANT_EXTRACT (JS clone 3 of 3): the third verbatim copy of formatBytes.
 * Three copies -> detector should recommend EXTRACT-CANDIDATE.
 */
export function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}
