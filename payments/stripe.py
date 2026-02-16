# payments/stripe.py
import os
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(...):
    if not STRIPE_AVAILABLE:
        return {"error": "Stripe temporarily unavailable"}

    # normal stripe code below
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": name,
                    },
                    "unit_amount": int(float(price) * 100),  # Convert to cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        return session.url
    except Exception as e:
        print("Stripe Error:", e)
        return None
