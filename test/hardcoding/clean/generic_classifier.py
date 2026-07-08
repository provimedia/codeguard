"""The generic mechanism the requirement actually asked for: classify ANY
domain by fetching its content and scoring keywords — no example literals."""
import urllib.request


KEYWORD_WEIGHTS = {
    'photovoltaik': ('solar', 3),
    'wechselrichter': ('solar', 2),
    'blockchain': ('krypto', 3),
    'wallet': ('krypto', 2),
}


def fetch_text(domain):
    with urllib.request.urlopen('https://' + domain, timeout=10) as resp:
        return resp.read().decode('utf-8', errors='replace').lower()


def classify(domain):
    text = fetch_text(domain)
    scores = {}
    for keyword, (branche, weight) in KEYWORD_WEIGHTS.items():
        if keyword in text:
            scores[branche] = scores.get(branche, 0) + weight
    return max(scores, key=scores.get) if scores else 'unbekannt'
