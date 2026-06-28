// Tiny math helpers used across the frontend.
export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
