import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_checkout_redirects(client, monkeypatch):
    class DummySession: url = "https://stripe.test/checkout"
    monkeypatch.setattr("stripe.checkout.Session.create", lambda **kw: DummySession())
    resp = client.get(reverse("checkout"))  # if you used Option A routes
    assert resp.status_code == 302
    assert resp["Location"].startswith("https://stripe.test/checkout")
