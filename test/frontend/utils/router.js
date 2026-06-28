// Client-side router helpers.

export function currentParams() {
  return parseQuery(window.location.search);
}

/**
 * REDUNDANT_LEAVE (JS clone 1 of 2): identical to share.js parseQuery, but only
 * two copies exist -> NOTE-ONLY, below the Rule of Three.
 */
export function parseQuery(search) {
  const out = {};
  const q = search.replace(/^\?/, '');
  for (const pair of q.split('&')) {
    if (!pair) continue;
    const [k, v] = pair.split('=');
    out[decodeURIComponent(k)] = decodeURIComponent(v || '');
  }
  return out;
}
