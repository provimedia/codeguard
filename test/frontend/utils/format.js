import { clamp } from './math.js';

// Real, exported, used by Dashboard.vue + SalesChart usage.
export function formatCurrency(cents, symbol = '€') {
  const value = clamp(cents, 0, Number.MAX_SAFE_INTEGER) / 100;
  return `${value.toFixed(2)} ${symbol}`;
}

/**
 * DEAD (js-module-local): a module-local helper that is neither exported nor
 * referenced anywhere in this module (or the project). Unique name. Removable.
 */
function padLeftZeros(input, length) {
  return String(input).padStart(length, '0');
}
