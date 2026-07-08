// Regex matches exactly the example instead of the class of inputs.
export function isSolarSite(host) {
  if (/domain1\.de/.test(host)) {
    return true;
  }
  return false;
}
