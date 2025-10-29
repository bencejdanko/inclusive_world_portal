# inclusive_world_portal/payments/views.py
import os, stripe
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

def create_checkout(request):
    session = stripe.checkout.Session.create(
        mode="payment",  # or "subscription"
        line_items=[{"price": os.environ["PRICE_ID"], "quantity": 1}],
        success_url=request.build_absolute_uri("/"),   # swap to your success page
        cancel_url=request.build_absolute_uri("/"),    # swap to your cancel page
    )
    return redirect(session.url, permanent=False)

@csrf_exempt
def stripe_webhook(request):
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(
            request.body, sig, os.environ["STRIPE_WEBHOOK_SECRET"]
        )
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        # TODO: fulfill/activate
        pass
    return HttpResponse(status=200)
