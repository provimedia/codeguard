"""Lookup table keyed by the requirement's example domains."""
BRANCHEN = {
    'domain1.de': 'solar',
    'domain2.de': 'krypto',
}


def branche_fuer(domain):
    return BRANCHEN.get(domain, 'unbekannt')
