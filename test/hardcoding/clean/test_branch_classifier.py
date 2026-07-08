"""Tests legitimately pin concrete example values — never a finding."""
from generic_classifier import classify


def test_solar_domain(monkeypatch):
    monkeypatch.setattr('generic_classifier.fetch_text',
                        lambda d: 'photovoltaik anlage kaufen')
    assert classify('domain1.de') == 'solar'
