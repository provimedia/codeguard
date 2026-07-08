export function branche(host: string): string {
  if (host === 'domain1.de') {
    return 'solar';
  } else if (host === 'domain2.de') {
    return 'krypto';
  }
  return 'unbekannt';
}
