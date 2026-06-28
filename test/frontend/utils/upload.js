// Upload UI helpers.

export function uploadLabel(file) {
  return `${file.name} (${formatBytes(file.size)})`;
}

/**
 * REDUNDANT_EXTRACT (JS clone 1 of 3): identical byte-size formatter, copied
 * verbatim into download.js and attachments.js. Same knowledge x3 -> EXTRACT.
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
