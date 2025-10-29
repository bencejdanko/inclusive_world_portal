# inclusive_world_portal/payments/tests/test_webhook.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_webhook_signature_ok(client, monkeypatch):
    def fake_construct_event(payload, sig, secret):
        return {"type": "checkout.session.completed", "data": {"object": {}}}
    monkeypatch.setattr("stripe.Webhook.construct_event", fake_construct_event)
    r = client.post(reverse("stripe-webhook"), data=b"{}", content_type="application/json")
    assert r.status_code == 200
