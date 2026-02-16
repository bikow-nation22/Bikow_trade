try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False


def create_checkout_session(*args, **kwargs):
    if not STRIPE_AVAILABLE:
        return {"error": "Stripe temporarily unavailable"}

    # If stripe exists, your real Stripe logic goes here
    return {"message": "Stripe is available but not configured yet"}
