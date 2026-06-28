// Social-share helpers.

export function shareTargetFromUrl(url) {
  const params = parseQuery(new URL(url).search);
  return params.via || 'default';
}

/**
 * REDUNDANT_LEAVE (JS clone 2 of 2): second (and final) copy of parseQuery.
 * Two copies only -> NOTE-ONLY, not EXTRACT-CANDIDATE.
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
